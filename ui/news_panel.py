"""
ui/news_panel.py - Panel lateral de noticias del Jarvis Launcher.

Rediseno v2 (modo workspace):
  - Cabecera con la pregunta "¿Qué está pasando en el mundo ahora?"
    (como pidio el usuario) y controles de refresco/configuracion.
  - Items con jerarquia tipografica limpia: fuente + hora arriba (dim),
    titulo destacado, preview de 2 lineas reservado bajo el titulo.
  - Estado vacio sin emojis grandes: mensaje sobrio + boton CONECTAR.
  - Panel lateral redimensionable arrastrando su borde; refresco automatico
    cada 10 minutos y manual (boton); click en noticia -> abre el lector de
    articulos a pantalla completa (ui/news_reader.py), que mantiene el enlace
    original ("Abrir original").

Estructura
----------
NewsPanel (QFrame):
  - Header: titulo + separador + boton refresco + boton config
  - NewsList (QScrollArea) con NewsItemWidget apilados
  - EmptyNewsView: estado "sin conexion" con boton CONECTAR
  - Footer: estado/fuentes/ultima hora

Mismo estilo visual que el resto (custom paint, sin QGraphicsEffect,
segun ADR-001).
"""

from __future__ import annotations

import threading
from datetime import datetime

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)

from core.feedback import play_click
from core.news import NewsItem, NewsService
from core.themes import ThemeManager


# ----------------------------------------------------------------------
# Item de noticia (entrada animada desde arriba)
# ----------------------------------------------------------------------


class NewsItemWidget(QFrame):
    """Una noticia individual limpia: meta (fuente+hora) y titulo.

    Sin preview apilado: la informacion completa se ve en el lector
    (news_reader.py con mini navegador), asi el panel respira.
    """

    itemClicked = pyqtSignal(object)  # NewsItem

    BASE_HEIGHT = 88

    def __init__(
        self,
        item: NewsItem,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.item = item
        self._theme = theme
        self._hovered = False
        self._grow: float = 0.35     # altura inicial pequeña (sale de arriba)
        self._alpha: float = 0.0

        self.setFixedHeight(self.BASE_HEIGHT)
        self.setMinimumHeight(1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)
        self._build_layout()

    def _build_layout(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        # Meta: fuente + hora (dim, compacto, uppercase)
        meta = QHBoxLayout()
        meta.setSpacing(8)
        self._source_label = QLabel(self.item.source.upper(), self)
        fs = QFont("Segoe UI", 7, QFont.Weight.DemiBold)
        fs.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self._source_label.setFont(fs)
        self._source_label.setStyleSheet("background: transparent; border: none;")
        meta.addWidget(self._source_label)
        self._time_label = QLabel(self.item.published, self)
        ft = QFont("Segoe UI", 7)
        self._time_label.setFont(ft)
        self._time_label.setStyleSheet("background: transparent; border: none;")
        meta.addWidget(self._time_label)
        meta.addStretch()
        lay.addLayout(meta)

        # Titulo (destacado, 2 lineas max)
        self._title_label = QLabel(self.item.title, self)
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("background: transparent; border: none;")
        self._title_label.setMaximumHeight(36)
        f = QFont("Segoe UI", 9, QFont.Weight.Bold)
        self._title_label.setFont(f)
        lay.addWidget(self._title_label)

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Animacion de entrada top-down
    # ------------------------------------------------------------------

    def play_entrance(self, delay_ms: int = 0, duration: int = 380) -> None:
        """Anima: crece de altura desde un minimo + fade-in de alpha."""
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, lambda: self._run_entrance(duration))
        else:
            self._run_entrance(duration)

    def _run_entrance(self, duration: int) -> None:
        grow = QPropertyAnimation(self, b"growIn")
        grow.setDuration(duration)
        grow.setStartValue(0.0)
        grow.setEndValue(1.0)
        grow.setEasingCurve(QEasingCurve.Type.OutCubic)

        alpha = QPropertyAnimation(self, b"fadeIn")
        alpha.setDuration(duration)
        alpha.setStartValue(0.0)
        alpha.setEndValue(1.0)
        alpha.setEasingCurve(QEasingCurve.Type.OutCubic)

        grow.start()
        alpha.start()
        self._grow_anim = grow
        self._alpha_anim = alpha

    # ------------------------------------------------------------------
    # Qt Properties
    # ------------------------------------------------------------------

    def _get_grow(self) -> float:
        return self._grow

    def _set_grow(self, val: float) -> None:
        self._grow = val
        # Altura real del widget: el layout empuja el resto hacia abajo,
        # generando el efecto "desplegar hacia abajo".
        self.setFixedHeight(max(1, int(self.BASE_HEIGHT * val)))
        self.update()

    growIn = pyqtProperty(float, _get_grow, _set_grow)

    def _get_alpha(self) -> float:
        return self._alpha

    def _set_alpha(self, val: float) -> None:
        self._alpha = val
        self.update()

    fadeIn = pyqtProperty(float, _get_alpha, _set_alpha)

    # ------------------------------------------------------------------
    # Pintura
    # ------------------------------------------------------------------

    @staticmethod
    def _rounded_rect_path(w: float, h: float, radius: float) -> QPainterPath:
        path = QPainterPath()
        r = radius
        path.moveTo(r, 0)
        path.lineTo(w - r, 0)
        path.quadTo(w, 0, w, r)
        path.lineTo(w, h - r)
        path.quadTo(w, h, w - r, h)
        path.lineTo(r, h)
        path.quadTo(0, h, 0, h - r)
        path.lineTo(0, r)
        path.quadTo(0, 0, r, 0)
        path.closeSubpath()
        return path

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        them = self._theme.theme
        alpha_scale = max(0.0, min(1.0, self._alpha))

        if h <= 2:
            super().paintEvent(event)
            p.end()
            return

        # Fondo de la tarjeta (translucido del tema)
        path = self._rounded_rect_path(w, h, 10)
        base = QColor(them.card_bg)
        base.setAlpha(int(235 * alpha_scale))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(base)
        p.drawPath(path)

        # Acento izquierdo (color de la fuente)
        if alpha_scale > 0.02:
            accent = QColor(them.accent)
            accent.setAlpha(int(150 * alpha_scale))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(accent)
            p.drawRoundedRect(4, 10, 3, max(0, h - 20), 2, 2)

        # Borde hover
        if self._hovered and alpha_scale > 0.2:
            halo = QColor(them.accent)
            halo.setAlpha(int(70))
            pen = QPen(halo, 1)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        # Titulo con hover highlight
        title_color = them.text
        if self._hovered:
            title_color = them.accent
        self._title_label.setStyleSheet(
            f"background: transparent; border: none; color: {title_color};"
        )

        # Fuente / hora
        dim = them.text_dim
        self._source_label.setStyleSheet(
            f"background: transparent; border: none; color: {dim};"
        )
        self._time_label.setStyleSheet(
            f"background: transparent; border: none; color: {dim};"
        )
        super().paintEvent(event)
        p.end()

    # ------------------------------------------------------------------
    # Click -> emitir item (el launcher abre el lector de articulos)
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            play_click()
            self.itemClicked.emit(self.item)
        super().mousePressEvent(event)


# ----------------------------------------------------------------------
# Estado vacio (sin fuentes configuradas) -> boton CONECTAR
# ----------------------------------------------------------------------


class EmptyNewsView(QWidget):
    """Mensaje sobrio + boton Conectar cuando no hay fuentes de noticias."""

    connectClicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = ThemeManager("obsidiana")
        self._build()

    def set_theme(self, theme: ThemeManager) -> None:
        self._theme = theme
        self._style_all()
        self.update()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        lay.addStretch()

        self._icon = QLabel("◉", self)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("background: transparent; border: none; font-size: 18px;")
        lay.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self._msg = QLabel(
            "Sin fuente de noticias conectada.\nElige una o pega tu propio enlace RSS.",
            self,
        )
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg.setWordWrap(True)
        lay.addWidget(self._msg, alignment=Qt.AlignmentFlag.AlignCenter)

        self._btn = QPushButton("CONECTAR", self)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setFixedHeight(36)
        self._btn.clicked.connect(self.connectClicked.emit)
        lay.addWidget(self._btn, alignment=Qt.AlignmentFlag.AlignCenter)

        lay.addStretch()
        self._style_all()

    def _style_all(self) -> None:
        them = self._theme.theme
        if not hasattr(self, "_msg"):
            return
        self._icon.setStyleSheet(
            f"background: transparent; border: none; color: {them.accent};"
            f"font-size: 18px;"
        )
        self._msg.setStyleSheet(
            f"background: transparent; border: none; color: {them.text_dim}; font-size: 12px;"
        )
        self._btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {them.accent_soft};
                color: {them.accent};
                border: 1px solid {them.accent};
                border-radius: 8px;
                padding: 0 22px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: {them.accent};
                color: {them.bg};
            }}
            """
        )


# ----------------------------------------------------------------------
# Panel principal de noticias
# ----------------------------------------------------------------------


class NewsPanel(QFrame):
    """
    Panel lateral de noticias con borde de redimension y refresco.

    Signals
    -------
    configureRequested : pide abrir el dialogo de conexion de fuentes.
    widthChanged : al redimensionar por borde (avisa al layout padre).
    readerRequested : (list[NewsItem], int) al pulsar una noticia -> abre el
        lector de articulos (news_reader.py) en lugar del navegador directo.
    """

    configureRequested = pyqtSignal()
    widthChanged = pyqtSignal(int)
    readerRequested = pyqtSignal(object, int)   # (items, index)
    _itemsFetched = pyqtSignal(object)   # list[NewsItem] desde hilo

    RESIZE_HANDLE = 6  # px del borde arrastrable

    MIN_WIDTH = 280
    MAX_WIDTH = 560

    def __init__(
        self,
        settings,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self._service = NewsService()
        self._loading = False
        self._resizing = False
        self._drag_start_x = 0
        self._drag_start_width = 0
        self._known_guids: set[str] = set()

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        self._itemsFetched.connect(self._apply_items)

        self._build_ui()
        self._apply_theme()
        self._load_state()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 6, 12)
        outer.setSpacing(10)

        # Header: pregunta del usuario + controles
        header = QVBoxLayout()
        header.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self._title = QLabel("¿QUÉ ESTÁ PASANDO EN EL MUNDO AHORA?", self)
        title_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self._title.setFont(title_font)
        self._title.setWordWrap(True)
        row1.addWidget(self._title, 1)

        self._refresh_btn = QPushButton("⟳", self)
        self._refresh_btn.setFixedSize(26, 26)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.setToolTip("Actualizar noticias")
        self._refresh_btn.clicked.connect(self.refresh)
        row1.addWidget(self._refresh_btn)

        self._config_btn = QPushButton("CONFIG", self)
        self._config_btn.setFixedHeight(26)
        self._config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._config_btn.setToolTip("Configurar fuentes de noticias")
        self._config_btn.clicked.connect(self.configureRequested.emit)
        row1.addWidget(self._config_btn)

        header.addLayout(row1)
        header.addWidget(self._mk_header_sep())

        outer.addLayout(header)

        # Scroll de items
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(10)
        self._list_layout.addStretch()
        self._scroll_area.setWidget(self._list_container)
        outer.addWidget(self._scroll_area, 1)

        # Estado vacio
        self._empty_view = EmptyNewsView(self)
        self._empty_view.connectClicked.connect(self.configureRequested.emit)
        self._empty_view.hide()

        # Footer / estado
        self._footer = QLabel("", self)
        self._footer.setStyleSheet("background: transparent; border: none;")
        self._footer.setFont(QFont("Segoe UI", 7))
        outer.addWidget(self._footer)

        # Timer de refresco automatico (10 min)
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self.refresh)
        self._auto_timer.start(10 * 60 * 1000)

    def _mk_header_sep(self) -> QFrame:
        sep = QFrame(self)
        sep.setFixedHeight(1)
        them = self._theme.theme
        sep.setStyleSheet(f"background: {them.card_border}; border: none;")
        return sep

    # ------------------------------------------------------------------
    # Estado inicial
    # ------------------------------------------------------------------

    def _load_state(self) -> None:
        if self._settings.news_enabled and self._settings.news_sources:
            self._set_connected()
            self.refresh()
        else:
            self._set_disconnected()

    def _set_connected(self) -> None:
        self._scroll_area.show()
        self._empty_view.hide()

    def _set_disconnected(self, msg: str = "") -> None:
        self._scroll_area.show()
        self._empty_view.setGeometry(12, 48, self.width() - 24, self.height() - 90)
        self._empty_view.show()
        self._footer.setText(msg or "Sin conexion de noticias")

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        them = self._theme.theme
        self.setStyleSheet(
            f"""
            NewsPanel {{
                background: {them.bg_alt};
                border: 1px solid {them.accent_soft};
                border-radius: 14px;
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: {them.text};
            }}
            """
        )
        self._title.setStyleSheet(
            f"background: transparent; border: none; color: {them.accent};"
            f"font-size: 8px; font-weight: bold; letter-spacing: 1px;"
        )
        accent = them.accent
        self._refresh_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {them.text_dim};
                border: 1px solid {them.card_border};
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {accent};
                border-color: {accent};
            }}
            """
        )
        self._config_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {them.text_dim};
                border: 1px solid {them.card_border};
                border-radius: 6px;
                padding: 0 8px;
                font-size: 8px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                color: {accent};
                border-color: {accent};
            }}
            """
        )
        self._empty_view.set_theme(self._theme)

    def refresh_theme(self) -> None:
        self._apply_theme()

    # ------------------------------------------------------------------
    # Redimension por borde
    # ------------------------------------------------------------------

    def _hit_resize(self, pos_x: int) -> bool:
        if self._settings.news_position == "left":
            return pos_x >= self.width() - self.RESIZE_HANDLE
        return pos_x <= self.RESIZE_HANDLE

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._hit_resize(
            int(event.position().x())
        ):
            self._resizing = True
            self._drag_start_x = int(event.globalPosition().x())
            self._drag_start_width = self.width()
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._resizing:
            delta = int(event.globalPosition().x()) - self._drag_start_x
            if self._settings.news_position == "right":
                new_w = self._drag_start_width - delta
            else:
                new_w = self._drag_start_width + delta
            new_w = max(self.MIN_WIDTH, min(self.MAX_WIDTH, int(new_w)))
            self.setFixedWidth(new_w)
            self.widthChanged.emit(new_w)
            event.accept()
            return
        if self._hit_resize(int(event.position().x())):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._resizing:
            self._resizing = False
            self._settings.news_width = self.width()
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_initial_width(self) -> None:
        self.setFixedWidth(self._settings.news_width)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Descarga noticias en hilo y actualiza la lista (signal a la UI)."""
        if self._loading or not self._settings.news_sources:
            return
        self._loading = True
        sources = list(self._settings.news_sources)
        self._footer.setText("Actualizando...")

        def _work() -> None:
            try:
                items = self._service.fetch_sources(sources)
            except Exception:  # noqa: BLE001
                items = []
            self._itemsFetched.emit(items)

        th = threading.Thread(target=_work, daemon=True)
        th.start()

    def _apply_items(self, items: list[NewsItem]) -> None:
        self._loading = False
        if not items:
            self._footer.setText("Sin noticias disponibles")
            if not self._settings.news_sources:
                self._set_disconnected()
            return

        # Limpiar items existentes
        for i in reversed(range(self._list_layout.count())):
            w = self._list_layout.itemAt(i).widget()
            if w is not None and isinstance(w, NewsItemWidget):
                self._list_layout.removeWidget(w)
                w.deleteLater()

        # Insertar nuevos: top-down con entrada escalonada
        self._current_items: list[NewsItem] = []
        for idx, item in enumerate(items[:12]):
            w = NewsItemWidget(item, self._theme, self._list_container)
            w.itemClicked.connect(self._open_item)
            self._current_items.append(item)
            self._list_layout.insertWidget(idx, w)
            w.play_entrance(delay_ms=min(idx * 45, 800), duration=340)

        # Guard de posicion del scroll arriba
        self._scroll_area.verticalScrollBar().setValue(0)

        self._known_guids = {(it.guid or it.url) for it in items}
        self._footer.setText(
            f"{len(items)} noticias · {datetime.now().strftime('%H:%M')}"
        )
        self._set_connected()

    def _open_item(self, item: NewsItem) -> None:
        """Click en noticia -> pide abrir el lector (news_reader, spec v2)."""
        items = getattr(self, "_current_items", [])
        index = items.index(item) if item in items else 0
        self.readerRequested.emit(list(items), index)

    # Eventos de redimension: mantener footer/estado vacio posicionados
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_empty_view") and not self._settings.news_sources:
            self._empty_view.setGeometry(
                12, 48, self.width() - 24, self.height() - 90
            )