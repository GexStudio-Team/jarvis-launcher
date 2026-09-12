"""
ui/news_reader.py - Lector de noticias a pantalla completa (spec v2, pts. 3-4).

En esta etapa el lector embebe un **mini navegador** (Chromium via
PyQt6-WebEngine / QWebEngineView) para ver el articulo completo desde Jarvis
con imagenes, CSS y todo el contenido real del sitio. Si PyQt6-WebEngine no
esta instalado, cae elegantemente al lector de texto (resumen del feed).

Estructura
----------
NewsReaderView (QWidget a pantalla completa):
  - Header: boton VOLVER, fuente + hora del articulo, recargar (⟳) y
    ABRIR ORIGINAL (navegador externo).
  - QSplitter horizontal redimensionable:
      * Panel izquierdo (lista): MiniNewsItem apilados; el actual resaltado.
      * Panel derecho: _MiniBrowser con Chromium embebido (o fallback texto).
  - Navegacion: <- / -> cambian de articulo; Escape vuelve al launcher.

Restricciones mantenidas: sin QGraphicsEffect (ADR-001); colores del
ThemeManager activo en toda la UI propia; PyQt6-WebEngine es la unica
dependencia opcional agregada (el fallback la hace no critica).

Rendimiento (ADR-009): el motor se pre-calienta desde JarvisUI (pre-warm a
~900 ms del boot), usa perfil persistente con cache HTTP en disco y bloquea
rastreadores/publicidad; el view no navega en el constructor y
JARVIS_DISABLE_WEBENGINE=1 fuerza el fallback en CI headless.
"""

from __future__ import annotations

import html as _html
import os
import webbrowser

from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.news import NewsItem
from core.themes import ThemeManager


# ----------------------------------------------------------------------
# Bloqueo de rastreadores / publicidad (optimizacion de carga, ADR-009)
# ----------------------------------------------------------------------

try:
    from PyQt6.QtWebEngineCore import (
        QWebEngineUrlRequestInterceptor as _ReqInterceptor,
    )
except ImportError:  # pragma: no cover - dependencia opcional ausente
    _ReqInterceptor = object  # type: ignore[assignment,misc]


class _TrackerBlocker(_ReqInterceptor):
    """Corta peticiones a rastreadores y publicidad conocidos.

    Reduce bytes y JavaScript por pagina (el contenido real del sitio
    no se toca: CSS, imagenes y fuentes de CDN conocidos se conservan).
    """

    _BLOCKED_HOSTS = (
        "doubleclick.net",
        "google-analytics.com",
        "googletagmanager.com",
        "googleadservices.com",
        "googlesyndication.com",
        "adservice.google.com",
        "connect.facebook.net",
        "scorecardresearch.com",
        "criteo.com",
        "taboola.com",
        "outbrain.com",
        "cookielaw.org",
        "onetrust.com",
        "mixpanel.com",
        "segment.io",
        "hotjar.com",
        "clarity.ms",
    )

    def interceptRequest(self, info) -> None:  # noqa: N802 (API Qt)
        host = info.requestUrl().host().lower()
        if any(host == d or host.endswith("." + d) for d in self._BLOCKED_HOSTS):
            info.block(True)


def _default_data_dir() -> str:
    """Directorio de datos del usuario (fallback cuando no hay APPDATA)."""
    return os.path.expanduser("~")


# ----------------------------------------------------------------------
# Mini-item de la lista izquierda (titulo + fuente/hora)
# ----------------------------------------------------------------------


class MiniNewsItem(QFrame):
    """Fila compacta de la lista del lector; click selecciona el articulo."""

    selected = pyqtSignal(int)

    def __init__(
        self,
        item: NewsItem,
        index: int,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._index = index
        self._theme = theme
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFixedHeight(76)
        self._build(item)

    def _build(self, item: NewsItem) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(3)

        meta = QHBoxLayout()
        meta.setSpacing(6)
        src = QLabel(item.source.upper(), self)
        f = QFont("Segoe UI", 7, QFont.Weight.DemiBold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        src.setFont(f)
        meta.addWidget(src)
        meta.addStretch()
        lay.addLayout(meta)

        title = QLabel(item.title, self)
        title.setWordWrap(True)
        title.setMaximumHeight(34)
        title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lay.addWidget(title)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._apply_style()
        self.update()

    def enterEvent(self, event) -> None:
        if not self._selected:
            self._apply_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._apply_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self._index)
        super().mousePressEvent(event)

    def _apply_style(self, hover: bool = False) -> None:
        them = self._theme.theme
        if self._selected:
            bg, border = them.accent_soft, them.accent
        elif hover:
            bg, border = "rgba(255,255,255,8)", them.card_border
        else:
            bg, border = "transparent", "transparent"
        self.setStyleSheet(
            f"MiniNewsItem {{"
            f" background: {bg};"
            f" border: 1px solid {border};"
            f" border-radius: 8px;"
            f"}}"
        )


# ----------------------------------------------------------------------
# Mini navegador embebido (Chromium) con fallback de texto
# ----------------------------------------------------------------------


class MiniBrowser(QWidget):
    """
    Muestra el articulo completo dentro del launcher.

    - Si PyQt6-WebEngine esta disponible: QWebEngineView cargando la URL
      real del articulo (imagenes, CSS, videos embebidos...).
    - Si no: QTextBrowser con el resumen del feed (modo lectura ligera).
    """

    def __init__(
        self,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._stack = QStackedWidget(self)

        # Fallback: lectura del feed (resumen con tipografia del tema)
        self._fallback = QTextBrowser(self._stack)
        self._fallback.setFrameShape(QFrame.Shape.NoFrame)
        self._fallback.setOpenExternalLinks(False)
        self._fallback.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._stack.addWidget(self._fallback)

        # Mini navegador (Chromium embebido) — disponible si esta instalado
        # Nota: el view se crea SIN navegar (ADR-009): los procesos de
        # Chromium arrancan al instanciarlo; la carga real ocurre en
        # show_article()/prewarm(). JARVIS_DISABLE_WEBENGINE=1 permite
        # probar la logica completa con el fallback de texto en CI headless.
        self._engine: QWidget | None = None
        if os.environ.get("JARVIS_DISABLE_WEBENGINE") != "1":
            try:
                from PyQt6.QtWebEngineCore import (
                    QWebEngineProfile,
                    QWebEngineSettings,
                )
                from PyQt6.QtWebEngineWidgets import QWebEngineView

                # Perfil persistente: cache HTTP en disco + almacen estable.
                # La 2a visita de un articulo carga assets desde cache (ADR-009).
                profile = QWebEngineProfile.defaultProfile()
                profile.setHttpCacheType(
                    QWebEngineProfile.HttpCacheType.DiskHttpCache
                )
                profile.setHttpCacheMaximumSize(100 * 1024 * 1024)  # 100 MB
                profile.setPersistentCookiesPolicy(
                    QWebEngineProfile.PersistentCookiesPolicy.
                    ForcePersistentCookies
                )
                profile.setPersistentStoragePath(
                    os.path.join(
                        os.environ.get("APPDATA", _default_data_dir()),
                        "JarvisLauncher",
                        "WebEngine",
                    )
                )
                # Bloqueo de rastreadores/publicidad (menos peticiones por pagina)
                profile.setUrlRequestInterceptor(_TrackerBlocker())

                self._engine = QWebEngineView(self._stack)
                self._engine.setZoomFactor(1.0)
                s = self._engine.settings()
                s.setAttribute(
                    QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True
                )
                # Sin autoplay de video: menos datos y menos ruido de carga
                s.setAttribute(
                    QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
                    True,
                )
                self._stack.addWidget(self._engine)
            except Exception:  # noqa: BLE001  (dependencia opcional ausente)
                self._engine = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    @property
    def uses_webengine(self) -> bool:
        return self._engine is not None

    def show_article(self, item: NewsItem, fallback_html: str) -> None:
        """Carga el articulo en el mini navegador (o en el texto de respaldo)."""
        if self._engine is not None:
            self._stack.setCurrentWidget(self._engine)
            self._engine.setUrl(QUrl(item.url))
        else:
            self._fallback.setHtml(fallback_html)
            self._stack.setCurrentWidget(self._fallback)
        # Scroll arriba (fallback)
        self._fallback.verticalScrollBar().setValue(0)

    def prewarm(self) -> None:
        """Calienta Chromium sin navegar a ninguna URL (ADR-009).

        Los procesos del motor (GPU/red/renderer) arrancan al instanciar el
        QWebEngineView en el constructor; este metodo es la explicita
        invitacion a no pagar ese arranque en el primer clic del usuario.
        """
        if self._engine is None:
            return

    def reload(self) -> None:
        if self._engine is not None:
            self._engine.reload()

    def set_theme(self, theme: ThemeManager) -> None:
        self._theme = theme
        them = self._theme.theme
        self._fallback.setStyleSheet(
            f"QTextBrowser {{ background: {them.bg}; }}"
        )


# ----------------------------------------------------------------------
# Lector principal (fullscreen, split-pane)
# ----------------------------------------------------------------------


class NewsReaderView(QWidget):
    """Lector de noticias a pantalla completa con split-pane redimensionable."""

    closeRequested = pyqtSignal()

    MIN_LIST = 180
    MAX_LIST = 380
    DEFAULT_LIST = 250

    def __init__(
        self,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._items: list[NewsItem] = []
        self._index = 0

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        root.addLayout(self._build_header())

        # Split-pane: lista | mini navegador
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setChildrenCollapsible(False)

        self._list_area = QScrollArea(self._splitter)
        self._list_area.setWidgetResizable(True)
        self._list_area.setFrameShape(QFrame.Shape.NoFrame)
        self._list_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 6, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        self._list_area.setWidget(self._list_container)

        self._browser = MiniBrowser(self._theme, self._splitter)

        self._splitter.addWidget(self._list_area)
        self._splitter.addWidget(self._browser)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([self.DEFAULT_LIST, 800])
        root.addWidget(self._splitter, 1)

        # Feedback ligero de carga del mini navegador
        if (engine := getattr(self._browser, "_engine", None)) is not None:
            engine.loadStarted.connect(self._on_load_started)
            engine.loadFinished.connect(self._on_load_finished)

        self._apply_theme()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(10)

        self._back_btn = QPushButton("← VOLVER", self)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setFixedHeight(34)
        self._back_btn.clicked.connect(self.closeRequested.emit)
        header.addWidget(self._back_btn)

        self._meta_label = QLabel("", self)
        self._meta_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        header.addWidget(self._meta_label, 1)

        self._reload_btn = QPushButton("⟳", self)
        self._reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reload_btn.setFixedSize(34, 34)
        self._reload_btn.setToolTip("Recargar el articulo en el mini navegador")
        self._reload_btn.clicked.connect(self._reload_page)
        header.addWidget(self._reload_btn)

        self._open_btn = QPushButton("ABRIR ORIGINAL ↗", self)
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.setFixedHeight(34)
        self._open_btn.setToolTip("Abrir el articulo completo en tu navegador")
        self._open_btn.clicked.connect(self._open_original)
        header.addWidget(self._open_btn)

        return header

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def set_theme(self, theme: ThemeManager) -> None:
        self._theme = theme
        self._apply_theme()

    def _apply_theme(self) -> None:
        them = self._theme.theme
        self.setStyleSheet(
            f"NewsReaderView {{ background: {them.bg}; }}"
        )
        # Header
        for btn in (self._back_btn, self._open_btn):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {them.accent_soft};
                    color: {them.accent};
                    border: 1px solid {them.accent};
                    border-radius: 8px;
                    padding: 0 16px;
                    font-size: 10px;
                    font-weight: bold;
                    letter-spacing: 2px;
                }}
                QPushButton:hover {{
                    background: {them.accent};
                    color: {them.bg};
                }}
                """
            )
        self._reload_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {them.text_dim};
                border: 1px solid {them.card_border};
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {them.accent};
                border-color: {them.accent};
            }}
            """
        )
        self._meta_label.setStyleSheet(
            f"background: transparent; border: none; color: {them.text_dim};"
            f"font-size: 11px; letter-spacing: 1px;"
        )
        # Lista
        self._list_area.setStyleSheet(
            f"QScrollArea {{ background: {them.bg_alt}; border: 1px solid {them.card_border};"
            f" border-radius: 10px; }}"
        )
        self._list_container.setStyleSheet(
            f"QWidget {{ background: {them.bg_alt}; }}"
        )
        self._list_area.viewport().setStyleSheet(
            f"background: {them.bg_alt}; border: none;"
        )
        # Splitter + navegador
        self._splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {them.card_border}; width: 2px; }}"
        )
        self._browser.set_theme(self._theme)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def set_items(self, items: list[NewsItem], index: int = 0) -> None:
        """Carga la lista de articulos y muestra el indice indicado."""
        if not items:
            return
        self._items = list(items)
        self._index = max(0, min(index, len(self._items) - 1))
        self._rebuild_list()
        self._render_document()

    def prewarm(self) -> None:
        """Calienta el mini navegador (Chromium) sin abrir el lector."""
        self._browser.prewarm()

    def _rebuild_list(self) -> None:
        # Limpiar mini-items previos
        for i in reversed(range(self._list_layout.count())):
            w = self._list_layout.itemAt(i).widget()
            if w is not None:
                self._list_layout.removeWidget(w)
                w.deleteLater()

        for idx, item in enumerate(self._items):
            w = MiniNewsItem(item, idx, self._theme, self._list_container)
            w.selected.connect(self._select)
            w.set_selected(idx == self._index)
            self._list_layout.insertWidget(idx, w)

    def _render_document(self) -> None:
        if not self._items:
            return
        item = self._items[self._index]
        them = self._theme.theme

        self._meta_label.setText(
            f"{item.source.upper()}  ·  {item.published}"
        )
        self._browser.show_article(
            item, self._build_article_html(item, them)
        )
        self._sync_list_selection()

    # ------------------------------------------------------------------
    # Fallback de texto (cuando no hay mini navegador)
    # ------------------------------------------------------------------

    @staticmethod
    def _split_readable(summary: str) -> tuple[str, str, str]:
        """Divide el resumen en (lead, pull_quote, body)."""
        sentences = [s.strip() for s in summary.split(". ") if s.strip()]
        if len(sentences) <= 1:
            return summary, "", ""
        lead = ". ".join(sentences[:2]) + "."
        quote = sentences[0] + "."
        body = ". ".join(sentences[2:]) + "." if len(sentences) > 2 else ""
        return lead, quote, body

    def _build_article_html(self, item: NewsItem, them) -> str:
        summary = (item.extra.get("summary") or "").strip()
        lead, quote, body = self._split_readable(summary)

        if not summary:
            lead = "El feed no incluye el resumen de este articulo."
            quote = ""

        title = _html.escape(item.title)
        if lead:
            cap = _html.escape(lead[0])
            rest = _html.escape(lead[1:])
            lead_html = (
                f"<span style='font-size:2.2em; color:{them.accent}; "
                f"font-weight:bold; font-family:Georgia;'>{cap}</span>{rest}"
            )
        else:
            lead_html = ""

        quote_html = (
            f"<div style='margin:26px 8px 26px 8px; padding:14px 22px;"
            f" border-left:3px solid {them.accent};"
            f" font-size:16px; font-style:italic; color:{them.text};'>"
            f"“{_html.escape(quote)}”"
            f"</div>"
        ) if quote else ""

        body_html = (
            f"<p style='font-size:14px; line-height:1.7; color:{them.text};"
            f" margin-top:22px;'>{_html.escape(body)}</p>"
        ) if body else ""

        return (
            f"<html><body style='background:{them.bg};'>"
            f"<div style='max-width:760px; margin:0 auto; padding:10px 18px 40px 18px;'>"
            f"<div style='font-size:26px; font-weight:bold; color:{them.text};"
            f" font-family:Georgia; line-height:1.3; margin-bottom:10px;'>{title}</div>"
            f"<div style='font-size:10px; letter-spacing:2px; color:{them.text_dim};"
            f" margin-bottom:24px;'>{_html.escape(item.source.upper())}"
            f" · {_html.escape(item.published)}</div>"
            f"<div style='font-size:17px; line-height:1.65; color:{them.text};'>"
            f"{lead_html}</div>"
            f"{quote_html}"
            f"<hr style='border:none; border-top:1px solid {them.card_border};"
            f" margin:22px 0 0 0;' />"
            f"{body_html}"
            f"</body></html>"
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _select(self, index: int) -> None:
        if index == self._index or not (0 <= index < len(self._items)):
            return
        self._index = index
        self._render_document()
        self.setFocus()

    def _sync_list_selection(self) -> None:
        for idx in range(self._list_layout.count()):
            w = self._list_layout.itemAt(idx).widget()
            if isinstance(w, MiniNewsItem):
                w.set_selected(idx == self._index)

    def _reload_page(self) -> None:
        self._browser.reload()

    def _open_original(self) -> None:
        item = self._items[self._index]
        if item.url:
            webbrowser.open(item.url)

    def _on_load_started(self) -> None:
        self._meta_label.setText("Cargando articulo…")

    def _on_load_finished(self, ok: bool) -> None:
        item = self._items[self._index] if self._items else None
        if item is None:
            return
        if ok:
            self._meta_label.setText(
                f"{item.source.upper()}  ·  {item.published}"
            )
        else:
            self._meta_label.setText(
                f"No se pudo cargar · {item.source.upper()} · use ABRIR ORIGINAL"
            )

    def update_position(self) -> None:
        """Reacomoda el lector al tamano de su padre (fullscreen)."""
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())

    # ------------------------------------------------------------------
    # Teclado: Escape cierra, flechas navegan
    # ------------------------------------------------------------------

    def handle_key(self, event) -> bool:
        """True si el evento fue consumido por el lector."""
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.closeRequested.emit()
            return True
        if key == Qt.Key.Key_Left and self._index > 0:
            self._select(self._index - 1)
            return True
        if key == Qt.Key.Key_Right and self._index < len(self._items) - 1:
            self._select(self._index + 1)
            return True
        return False

    def keyPressEvent(self, event) -> None:
        if not self.handle_key(event):
            super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        self.update_position()
        self.setFocus()
        super().showEvent(event)

    def resizeEvent(self, event) -> None:
        self.update_position()
        super().resizeEvent(event)