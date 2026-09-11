"""
ui/news_reader.py - Lector de noticias a pantalla completa (spec v2, pts. 3-4).

Decisiones del diseno v2 (ver ADR de la rama feat/news-reader):
  - C1: split-pane redimensionable — lista compacta a la izquierda y lectura
    larga a la derecha (QSplitter), navegando sin volver al panel.
  - B4: el contenido mostrado es el que trae el feed (summary/lead + body);
    cuando el feed no incluye el cuerpo completo, el boton "Abrir original"
    deja la lectura en el navegador.
  - Tipografia de lectura larga: titulo grande, meta en dim, LEAD destacado
    con capitular + barra de acento, PULL-QUOTE en cursiva y divisores
    tipograficos. La busca leer sin filas de 80 caracteres: columna centrada
    y aire lateral.

Restricciones mantenidas: sin QGraphicsEffect (ADR-001), cero dependencias
nuevas (PyQt6 + stdlib), colores siempre del ThemeManager activo.

Estructura
----------
NewsReaderView (QWidget a pantalla completa):
  - Header: boton VOLVER, fuente + hora del articulo, boton ABRIR ORIGINAL.
  - QSplitter horizontal redimensionable:
      * Panel izquierdo (lista): MiniNewsItem apilados; el actual resaltado.
      * Panel derecho (lectura): QTextBrowser con el articulo en HTML del tema.
  - Navegacion: <- / -> cambian de articulo; Escape vuelve al launcher.
"""

from __future__ import annotations

import html as _html
import webbrowser

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.feedback import play_click
from core.news import NewsItem
from core.themes import ThemeManager


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
            play_click()
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

        # Split-pane: lista | lectura
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

        self._doc_area = QScrollArea(self._splitter)
        self._doc_area.setWidgetResizable(True)
        self._doc_area.setFrameShape(QFrame.Shape.NoFrame)
        self._doc = QTextBrowser(self._doc_area)
        self._doc.setOpenExternalLinks(False)
        self._doc.setFrameShape(QFrame.Shape.NoFrame)
        self._doc.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._doc_area.setWidget(self._doc)

        self._splitter.addWidget(self._list_area)
        self._splitter.addWidget(self._doc_area)
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([self.DEFAULT_LIST, 800])
        root.addWidget(self._splitter, 1)

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
        if self._items:
            self._render_document()

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
        # Lectura
        self._doc_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._doc_area.viewport().setStyleSheet("background: transparent; border: none;")
        split_handle = f"background: {them.card_border}; width: 2px;"
        self._splitter.setStyleSheet(
            f"QSplitter::handle {{ {split_handle} }}"
        )
        self._doc.viewport().setAutoFillBackground(False)

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

    # ------------------------------------------------------------------
    # Conenido del articulo
    # ------------------------------------------------------------------

    def _render_document(self) -> None:
        if not self._items:
            return
        item = self._items[self._index]
        them = self._theme.theme

        self._meta_label.setText(
            f"{item.source.upper()}  ·  {item.published}"
        )
        self._doc.setHtml(self._build_article_html(item, them))

        # Scroll arriba al cambiar de articulo
        self._doc.verticalScrollBar().setValue(0)
        self._sync_list_selection()

    @staticmethod
    def _split_readable(summary: str) -> tuple[str, str, str]:
        """Divide el resumen en (lead, pull_quote, body).

        - lead: primeras ~2 oraciones (gancho destacado).
        - pull_quote: primera oracion citable (si hay mas de una).
        - body: el resto como parrafo de lectura.
        """
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

        # Fallo de contenido: si no hay resumen, se muestra el titulo y el
        # boton "Abrir original" queda como camino principal.
        if not summary:
            lead = "El feed no incluye el resumen de este articulo."
            quote = ""

        title = _html.escape(item.title)
        # Capitular: primera letra del lead en grande (hook tipografico inline)
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
        self._doc.setFocus()

    def _sync_list_selection(self) -> None:
        for idx in range(self._list_layout.count()):
            w = self._list_layout.itemAt(idx).widget()
            if isinstance(w, MiniNewsItem):
                w.set_selected(idx == self._index)

    def _open_original(self) -> None:
        play_click()
        item = self._items[self._index]
        if item.url:
            webbrowser.open(item.url)

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