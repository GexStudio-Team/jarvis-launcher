"""
ui/jarvis_ui.py - Ventana principal del Jarvis Launcher (v2 workspace).

Cambios de la v2 (modo foco / workspace, solicitud del usuario):
  1. Comportamiento de ventana: el launcher queda SIEMPRE al frente
     (z-order + foco), se oculta al elegir un modo (deja la vista al
     frente) y se invoca desde cualquier app con el atajo global
     Ctrl+Shift+Espacio (core/hotkey.py) o desde la bandeja
     (core/tray.py). El ✕ ahora oculta a bandeja en lugar de cerrar.
  2. Saludo dinamico: por franja horaria + adjetivo rotativo por arranque
     (core/greeting.py) o el NOMBRE REAL del usuario cuando la cuenta de
     GitHub esta vinculada (core/github_link.py).
  3. Panel de noticias rediseñado con la cabecera "¿Qué está pasando en
     el mundo ahora?" (ver news_panel.py).
  4. Cards en modo workspace sobrio (ver mode_card.py): monograma en vez
     de emoji gigante. Los modos (Gaming/Trabajo/Estudio) se CONSERVAN.

Se mantienen las restricciones del ADR-001: sin QGraphicsEffect
(QGraphicsOpacityEffect / QGraphicsDropShadowEffect). Fades con windowOpacity
nativa y pintura manual de todos los efectos.
"""

from __future__ import annotations

import math
import os
import random
import sys
from datetime import datetime

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QRadialGradient,
    QPen,
    QPainter,
)
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from core.greeting import ADJECTIVES, greeting_for
from core.hotkey import GlobalHotkey
from core.notifier import notify
from core.state import StateManager
from core.themes import ThemeManager
from core.settings import SettingsManager
from core.tray import Tray
from ui.mode_card import ModeCard
from ui.news_panel import NewsPanel
from ui.news_reader import NewsReaderView
from ui.settings_dialog import SettingsDialog, ConnectDialog

# ======================================================================
# Efectos de fondo
# ======================================================================


class Particle:
    """Particula flotante animada en el fondo (color del tema)."""

    def __init__(self, width: int, height: int, accent: str) -> None:
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.size = random.uniform(1.0, 3.0)
        self.speed_x = random.uniform(-0.3, 0.3)
        self.speed_y = random.uniform(-0.5, -0.1)
        self.opacity = random.uniform(30, 120)
        self.color = QColor(accent)
        self.color.setAlpha(int(self.opacity))
        self.canvas_w = width
        self.canvas_h = height

    def update(self) -> None:
        self.x += self.speed_x
        self.y += self.speed_y
        if self.y < -10:
            self.y = self.canvas_h + 10
            self.x = random.uniform(0, self.canvas_w)
        if self.x < -10:
            self.x = self.canvas_w + 10
        elif self.x > self.canvas_w + 10:
            self.x = -10


# ======================================================================
# Overlays boot / flash (temas)
# ======================================================================


class BootOverlay(QWidget):
    """Pantalla de boot tipo arranque de sistema (colores del tema)."""

    def __init__(self, app_name: str, version: str, theme: ThemeManager, parent: QWidget) -> None:
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._theme = theme
        self._app_name = app_name
        self._version = version
        self._fade: float = 1.0
        self._progress: float = 0.0
        self._dots = 0

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(32)

        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_dots)
        self._dots_timer.start(220)

    def _tick_anim(self) -> None:
        if self._progress < 0.95:
            self._progress = min(0.95, self._progress + 0.012)
        self.update()

    def _animate_dots(self) -> None:
        self._dots = (self._dots + 1) % 4
        self.update()

    def fade_out(self, on_done=None) -> None:
        self._anim_timer.stop()
        self._dots_timer.stop()
        anim = QPropertyAnimation(self, b"fade")
        anim.setDuration(500)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        if on_done:
            anim.finished.connect(on_done)
        anim.finished.connect(self.deleteLater)
        anim.start()
        self._boot_fade = anim

    # Qt Property fade
    def _get_fade(self) -> float:
        return self._fade

    def _set_fade(self, val: float) -> None:
        self._fade = val
        self.update()

    fade = pyqtProperty(float, _get_fade, _set_fade)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        f = self._fade
        them = self._theme.theme
        accent = QColor(them.accent)

        # Fondo solido del tema
        p.fillRect(0, 0, w, h, QColor(them.bg))
        # Velo sutil durante el fade-out (opacidad creciente del fondo)
        p.fillRect(0, 0, w, h, ThemeManager.rgba(them.bg, int(140 * (1.0 - f))))

        # Titulo con glow
        title_font = QFont("Segoe UI", 40, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)
        p.setFont(title_font)
        fm = p.fontMetrics()
        title_w = fm.horizontalAdvance(self._app_name)
        title_h = fm.height()
        title_x = (w - title_w) // 2
        title_y = h // 2 - 50

        # Glow
        glow = QRadialGradient(
            float(w / 2), float(title_y + title_h / 2), float(title_w * 0.6)
        )
        glow.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), int(70 * f)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawRoundedRect(title_x - 60, title_y - 40, title_w + 120, title_h + 80, 40, 40)

        # Texto principal
        p.setPen(QColor(accent.red(), accent.green(), accent.blue(), int(235 * f)))
        p.drawText(title_x, title_y + title_h - 10, self._app_name)
        p.setPen(QColor(accent.red(), accent.green(), accent.blue(), int(60 * f)))
        p.drawText(title_x + 2, title_y + title_h - 8, self._app_name)

        # Version
        p.setPen(ThemeManager.rgba(them.text_dim, int(80 * f)))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(w // 2 - 60, title_y + title_h + 10, f"v{self._version}")

        # Barra de progreso
        bar_w, bar_h = 340, 4
        bx = (w - bar_w) // 2
        by = title_y + title_h + 40
        p.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), int(50 * f)), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(bx, by, bar_w, bar_h, 2, 2)

        p.setPen(Qt.PenStyle.NoPen)
        filled = int(bar_w * self._progress)
        if filled > 4:
            grad = QLinearGradient(bx, by, bx + bar_w, by)
            grad.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), int(180 * f)))
            grad.setColorAt(1.0, QColor(accent.lighter(150).red(), accent.lighter(150).green(), accent.lighter(150).blue(), int(220 * f)))
            p.setBrush(grad)
            p.drawRoundedRect(bx, by, filled, bar_h, 2, 2)

        # Status
        p.setPen(QColor(accent.red(), accent.green(), accent.blue(), int(150 * f)))
        p.setFont(QFont("Segoe UI", 12))
        status = "INICIANDO SISTEMA" + "." * self._dots
        p.drawText(w // 2 - 80, by + 30, status)

        # Fecha
        p.setPen(ThemeManager.rgba(them.text_dim, int(70 * f)))
        p.setFont(QFont("Segoe UI", 9))
        fecha = datetime.now().strftime("%d %b %Y - %H:%M")
        p.drawText(w - 160, h - 20, fecha)


class FlashOverlay(QWidget):
    """Overlay de flash a todo color al seleccionar un modo."""

    def __init__(self, color: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._color = QColor(color)
        self._alpha: float = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

    def _get_alpha(self) -> float:
        return self._alpha

    def _set_alpha(self, val: float) -> None:
        self._alpha = val
        self.update()

    alpha = pyqtProperty(float, _get_alpha, _set_alpha)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        color = QColor(self._color)
        color.setAlpha(int(255 * self._alpha))
        p.fillRect(self.rect(), color)

    def animate(self) -> QPropertyAnimation:
        anim = QPropertyAnimation(self, b"alpha")
        anim.setDuration(450)
        anim.setKeyValueAt(0.0, 0.0)
        anim.setKeyValueAt(0.3, 0.25)
        anim.setKeyValueAt(0.7, 0.15)
        anim.setKeyValueAt(1.0, 0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(self.deleteLater)
        anim.start()
        return anim


# ======================================================================
# Ventana principal
# ======================================================================


class JarvisUI(QWidget):
    """Ventana tipo Jarvis con layout compacto, temas y panel de noticias."""

    HUD_RING_RADIUS_RATIO = 0.30
    RING_SPEEDS = [0.3, -0.5, 0.8]

    BOOT_DURATION_MS = 1300
    TYPEWRITER_MS = 16

    def __init__(
        self,
        config: dict,
        settings: SettingsManager | None = None,
        on_mode_selected=None,
    ) -> None:
        super().__init__()
        self._config = config
        self._on_mode_selected = on_mode_selected
        self._settings = settings or SettingsManager()
        self._theme = ThemeManager(self._settings.theme)
        self._force_quit = False  # True solo cuando se sale de verdad desde la bandeja

        # Estado animacion
        self._ring_angles = [0.0, 45.0, 90.0]
        self._particles: list[Particle] = []
        self._scan_y: float = 0.0
        self._is_launching = False
        self._launch_message = ""

        # Beam
        self._beam_card: ModeCard | None = None
        self._beam_t: float = 0.0
        self._beam_active = False

        # Estado
        self._state = StateManager()

        # Ventana
        self.setWindowTitle("J.A.R.V.I.S. Launcher")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumSize(1200, 720)
        self._center_on_screen()

        # Fondo animado
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._apply_theme_particles()
        self._build_ui()
        self._setup_system_integration()
        self._run_boot_sequence()

    # ------------------------------------------------------------------
    # Integracion con el sistema (bandeja + atajo global + z-order)
    # ------------------------------------------------------------------

    def _setup_system_integration(self) -> None:
        """Bandeja del sistema, atajo global y foco diactivo al abrir."""

        # Bandeja: vive en background, doble click o menu la traen al frente
        self._tray = Tray(
            on_show=self.show_and_raise,
            on_quit=self.quit_app,
            accent=self._theme.theme.accent,
        )
        self._tray.show()

        # Atajo global Ctrl+Shift+Espacio: convoca/oculta el launcher
        self._hotkey = GlobalHotkey(self.toggle_visibility)
        app = QApplication.instance()
        if app is not None:
            app.installNativeEventFilter(self._hotkey)
            self._hotkey.register()

    def show_and_raise(self) -> None:
        """Muestra la ventana forzando que quede al frente y con foco."""
        self.show()
        self.raise_()
        self.activateWindow()
        if self.isMinimized():
            self.showNormal()

    def toggle_visibility(self) -> None:
        """Atajo global: alterna mostrar/ocultar (sin cerrar)."""
        if self.isVisible():
            self.hide()
        else:
            self.show_and_raise()

    def quit_app(self) -> None:
        """Salida real desde la bandeja (desregistra atajo y cierra)."""
        self._force_quit = True
        try:
            self._hotkey.unregister()
            app = QApplication.instance()
            if app is not None:
                app.removeNativeEventFilter(self._hotkey)
        except Exception:  # pragma: no cover
            pass
        self._tray.hide()
        app.quit() if (app := QApplication.instance()) is not None else None

    # ------------------------------------------------------------------
    # Ocultar a bandeja en vez de cerrar (opcion C del diseno)
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Al pulsar ✕ se oculta a la bandeja en lugar de salir (si esta activa)."""
        if self._force_quit or not self._settings.tray_enabled:
            event.accept()
            return
        event.ignore()
        self.hide()
        notify(
            "J.A.R.V.I.S.",
            "Sigue en la bandeja. Atajo global: Ctrl+Shift+Espacio.",
        )

    # ------------------------------------------------------------------
    # Geometria
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        w = min(1480, geo.width() - 60)
        h = min(920, geo.height() - 60)
        x = geo.x() + (geo.width() - w) // 2
        y = geo.y() + (geo.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def _apply_theme_particles(self) -> None:
        w, h = self.width(), self.height()
        self._particles = [
            Particle(w, h, self._theme.theme.accent) for _ in range(70)
        ]

    # ------------------------------------------------------------------
    # UI Layout (compacto, sin huecos)
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Layout raiz: noticias (lateral) | area central
        self._root_layout = QHBoxLayout(self)
        self._root_layout.setContentsMargins(28, 18, 28, 14)
        self._root_layout.setSpacing(18)

        # ---- Area central ----
        self._center_widget = QWidget(self)
        self._center_layout = QVBoxLayout(self._center_widget)
        self._center_layout.setContentsMargins(20, 6, 20, 6)
        self._center_layout.setSpacing(12)

        self._build_top_bar()
        self._center_layout.addLayout(self._top_layout)

        # Titulo (ocupara proporcion moderada, sin estirar todo)
        self._build_title()
        self._center_layout.addWidget(self._title_container, 1)

        # Cards (centradas, respirables pero compactas)
        self._build_cards()
        self._center_layout.addWidget(
            self._cards_container, 3, Qt.AlignmentFlag.AlignCenter
        )

        # Estado (abajo)
        self._build_status_bar()
        self._center_layout.addLayout(self._status_bar)

        # ---- Panel de noticias ----
        self._news_panel = NewsPanel(self._settings, self._theme, self)
        self._news_panel.configureRequested.connect(self._open_connect_dialog)
        self._news_panel.widthChanged.connect(self._on_news_width_changed)
        self._news_panel.readerRequested.connect(self._open_reader)
        self._news_panel.set_initial_width()

        # ---- Lector de articulos (fullscreen, creado bajo demanda) ----
        self._news_reader: NewsReaderView | None = None

        # ---- Pre-warm de Chromium (ADR-009) ----
        # Calienta el motor web en segundo plano tras el boot para que el
        # primer clic en una noticia no pague el arranque de Chromium.
        QTimer.singleShot(900, self._prewarm_webengine)

        # Insertar segun posicion
        self._apply_news_panel_position()

        # Aplicar colores del tema a los widgets QSS
        self._apply_theme_styles()

    def _build_top_bar(self) -> None:
        self._top_layout = QHBoxLayout()
        self._top_layout.setContentsMargins(4, 0, 4, 0)
        self._top_layout.setSpacing(10)

        logo = QLabel("J.A.R.V.I.S.", self._center_widget)
        logo.setStyleSheet(
            "background: transparent; border: none;"
            "font-size: 14px; font-weight: bold; letter-spacing: 4px;"
        )
        self._logo_label = logo
        self._top_layout.addWidget(logo)
        self._top_layout.addStretch()

        # Ruedita de ajustes (tema + noticias)
        self._settings_btn = QPushButton("⚙", self._center_widget)
        self._settings_btn.setFixedSize(36, 36)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.setToolTip("Panel de control (temas y noticias)")
        self._settings_btn.clicked.connect(self.open_settings)
        self._top_layout.addWidget(self._settings_btn)

        # Auto-inicio
        self._setup_btn = QPushButton("Configurar auto-inicio", self._center_widget)
        self._setup_btn.setFixedHeight(36)
        self._setup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_btn.clicked.connect(self._toggle_startup)
        self._top_layout.addWidget(self._setup_btn)

        # Cerrar
        self._close_btn = QPushButton("✕", self._center_widget)
        self._close_btn.setFixedSize(36, 36)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.close)
        self._top_layout.addWidget(self._close_btn)

        self._style_top_bar()

    def _style_top_bar(self) -> None:
        them = self._theme.theme
        accent = them.accent
        if hasattr(self, "_logo_label"):
            self._logo_label.setStyleSheet(
                f"background: transparent; border: none;"
                f"color: {accent}; font-size: 14px; font-weight: bold; letter-spacing: 4px;"
            )
        corners = "border: none; background: transparent;"
        for btn in (self._settings_btn, self._close_btn):
            btn.setStyleSheet(
                f"QPushButton {{ {corners} color: {them.text_dim}; font-size: 15px; }}"
                f"QPushButton:hover {{ color: {accent}; }}"
            )
        self._setup_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {them.accent_soft};
                color: {accent};
                border: 1px solid {QColor(accent).name()};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 11px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {accent};
                color: {them.bg};
            }}
            """
        )

    def _build_title(self) -> None:
        self._title_container = QWidget(self._center_widget)
        self._title_container.setStyleSheet("background: transparent;")
        tl = QVBoxLayout(self._title_container)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(6)

        self._greeting_label = QLabel("", self._title_container)
        self._greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._greeting_label.setWordWrap(True)
        tl.addWidget(self._greeting_label)
        self._greeting_label.setStyleSheet(
            "background: transparent; border: none; color: rgba(255,255,255,200);"
            "font-size: 20px; font-weight: 300; letter-spacing: 1px;"
        )

    def _build_cards(self) -> None:
        self._cards_container = QWidget(self._center_widget)
        self._cards_container.setStyleSheet("background: transparent;")
        self._cards_layout = QHBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(26)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._mode_cards: dict[str, ModeCard] = {}
        modes = self._config.get("modes", {})
        for idx, (mode_id, mode_data) in enumerate(modes.items()):
            card = ModeCard(
                mode_id=mode_id,
                name=mode_data.get("name", mode_id),
                icon=mode_data.get("icon", "?"),
                color=mode_data.get("color", "#00FFFF"),
                description=mode_data.get("description", ""),
                theme=self._theme,
                parent=self._cards_container,
            )
            apps = mode_data.get("apps", [])
            card.set_app_count(len(apps))
            card.modeClicked.connect(self._on_card_clicked)
            self._mode_cards[mode_id] = card
            self._cards_layout.addWidget(card)
            # Entrada escalonada
            card.play_entrance(delay_ms=250 + idx * 140)

    def _build_status_bar(self) -> None:
        self._status_bar = QHBoxLayout()
        self._status_bar.setContentsMargins(4, 6, 4, 0)
        self._status_label = QLabel("SISTEMA LISTO", self._center_widget)
        self._status_label.setStyleSheet(
            "background: transparent; border: none; color: rgba(0,255,255,120);"
            "font-size: 10px; letter-spacing: 3px;"
        )
        self._status_bar.addWidget(self._status_label)
        self._status_bar.addStretch()
        version_label = QLabel(
            f"v{self._config.get('version', '1.0.0')}", self._center_widget
        )
        version_label.setStyleSheet(
            "background: transparent; border: none; color: rgba(255,255,255,50); font-size: 10px;"
        )
        self._status_bar.addWidget(version_label)

    # ------------------------------------------------------------------
    # Panel de noticias
    # ------------------------------------------------------------------

    def _apply_news_panel_position(self) -> None:
        """Acomoda el panel a la izquierda o derecha segun los ajustes."""
        # Remover si ya esta
        try:
            self._root_layout.removeWidget(self._news_panel)
        except Exception:  # noqa: BLE001
            pass
        self._root_layout.removeWidget(self._center_widget)

        pos = self._settings.news_position
        if not self._settings.news_enabled:
            # Solo area central (sin panel)
            if self._news_panel is not None:
                self._news_panel.hide()
            self._root_layout.addWidget(self._center_widget, 1)
            return

        self._news_panel.show()
        idx = 0 if pos == "left" else 2
        self._root_layout.insertWidget(idx, self._news_panel, 0)
        self._root_layout.insertWidget(1, self._center_widget, 1)
        # Forzar medida inicial
        self._news_panel.set_initial_width()

    def _on_news_width_changed(self, value: int) -> None:
        self._settings.news_width = value

    # ------------------------------------------------------------------
    # Lector de articulos (spec v2 pts. 3-4)
    # ------------------------------------------------------------------

    def _open_reader(self, items: list, index: int = 0) -> None:
        """Abre el lector de noticias a pantalla completa sobre el launcher."""
        if not items:
            return
        if self._news_reader is None:
            self._news_reader = NewsReaderView(self._theme, self)
            self._news_reader.closeRequested.connect(self._close_reader)
        self._news_reader.set_items(items, index)
        self._news_reader.set_theme(self._theme)
        self._news_reader.update_position()
        self._news_reader.show()
        self._news_reader.raise_()
        # Fade de entrada corto (110 ms, ADR-009): respuesta casi instantanea
        fade = QPropertyAnimation(self._news_reader, b"windowOpacity")
        fade.setDuration(110)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start()
        self._reader_fade = fade

    def _prewarm_webengine(self) -> None:
        """Calienta Chromium en segundo plano tras el boot (ADR-009).

        El primer clic en una noticia solo navega a la URL (setUrl); el
        arranque de los procesos de Chromium ya ocurrio oculto aqui.
        """
        if self._news_reader is None:
            self._news_reader = NewsReaderView(self._theme, self)
            self._news_reader.closeRequested.connect(self._close_reader)
        self._news_reader.hide()

    def _close_reader(self) -> None:
        """Vuelve del lector al launcher."""
        if self._news_reader is None:
            return
        self._news_reader.hide()
        self.show_and_raise()

    def open_settings(self) -> None:
        """Ruedita de ajustes."""
        dlg = SettingsDialog(self._settings, self._theme, self)
        dlg.exec()

    def refresh_greeting(self) -> None:
        """Re-escribe el saludo con el nombre real recien vinculado (GitHub)."""
        self._full_greeting = self._build_greeting()
        self._greeting_label.setText(self._full_greeting)

    def toggle_startup(self) -> None:
        """Publico para el dialogo de ajustes (auto-inicio)."""
        had_auto = self._startup_configured()
        self._toggle_startup()
        if had_auto != self._startup_configured():
            self._status_label.setText(
                "AUTO-INICIO ACTIVADO" if self._startup_configured()
                else "AUTO-INICIO DESACTIVADO"
            )

    def _startup_configured(self) -> bool:
        startup_dir = os.path.join(
            os.environ["APPDATA"],
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        return any(
            os.path.exists(os.path.join(startup_dir, f))
            for f in ("JarvisLauncher.vbs", "JarvisLauncher.bat")
        )

    def _open_connect_dialog(self) -> None:
        dlg = ConnectDialog(self._settings, self._theme, self)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self._settings.news_enabled = True
            self.apply_news_panel()
            self._news_panel.refresh()

    def refresh_news(self) -> None:
        """Publico para refrescar noticias tras conectar fuente."""
        self._news_panel.refresh()

    # ------------------------------------------------------------------
    # Tema (publico para el dialogo)
    # ------------------------------------------------------------------

    def apply_theme(self) -> None:
        """Aplica el tema activo a todos los elementos (llamado por ajustes)."""
        self._theme = ThemeManager(self._settings.theme)
        self._apply_theme_particles()
        self._apply_theme_styles()
        self._news_panel.refresh_theme()
        self._tray.set_accent(self._theme.theme.accent)
        self.update()

    def _apply_theme_styles(self) -> None:
        them = self._theme.theme
        self.setStyleSheet(
            f"JarvisUI {{ background: {them.bg}; color: {them.text}; }}"
        )
        self._style_top_bar()
        # Greeting
        self._greeting_label.setStyleSheet(
            f"background: transparent; border: none; color: {them.text};"
            f"font-size: 20px; font-weight: 300; letter-spacing: 1px;"
        )
        # Status bar
        self._status_label.setStyleSheet(
            f"background: transparent; border: none; color: {them.accent};"
            f"font-size: 10px; letter-spacing: 3px;"
        )

    # ------------------------------------------------------------------
    # Secuencia de boot
    # ------------------------------------------------------------------

    def _run_boot_sequence(self) -> None:
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(500)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start()
        self._fade_anim = fade

        self._boot_overlay = BootOverlay(
            app_name=self._config.get("app_name", "J.A.R.V.I.S."),
            version=self._config.get("version", "1.0.0"),
            theme=self._theme,
            parent=self,
        )
        self._boot_overlay.show()
        self._boot_overlay.raise_()

        QTimer.singleShot(
            self.BOOT_DURATION_MS,
            lambda: self._boot_overlay.fade_out(self._start_typewriter),
        )

    def _start_typewriter(self) -> None:
        full_text = self._build_greeting()
        self._greeting_pos = 0
        self._type_timer = QTimer(self)
        self._type_timer.timeout.connect(self._type_char)
        self._type_timer.start(self.TYPEWRITER_MS)
        self._full_greeting = full_text
        self._type_char()
        self._update_status_ready()

    def _build_greeting(self) -> str:
        """Saludo dinamico: franja horaria + nombre real o adjetivo rotativo."""
        # Nombre real si la cuenta GitHub esta vinculada
        display_name = self._settings.github_name or ""
        if not display_name:
            # Adjetivo rotativo: el indice avanza en cada arranque
            idx = self._settings.greeting_adjective_index
            display_name = ADJECTIVES[idx % len(ADJECTIVES)]
            self._settings.greeting_adjective_index = (idx + 1) % len(ADJECTIVES)
        return greeting_for(datetime.now(), display_name)

    def _type_char(self) -> None:
        self._greeting_pos += 2
        self._greeting_label.setText(self._full_greeting[: self._greeting_pos])
        if self._greeting_pos >= len(self._full_greeting):
            self._type_timer.stop()

    def _update_status_ready(self) -> None:
        last = self._state.get_last_mode()
        if last is None:
            self._status_label.setText("SISTEMA LISTO")
            return
        try:
            at = datetime.fromisoformat(last["at"])
            now = datetime.now(at.tzinfo)
            delta = (now - at).total_seconds()
            if delta < 60:
                ago = "ahora mismo"
            elif delta < 3600:
                ago = f"hace {int(delta // 60)} min"
            else:
                ago = f"hace {int(delta // 3600)} h"
            self._status_label.setText(
                f"ULTIMO MODO: {last.get('name', last['id']).upper()} - {ago}"
            )
        except (ValueError, KeyError):
            self._status_label.setText("SISTEMA LISTO")

    # ------------------------------------------------------------------
    # Interaccion
    # ------------------------------------------------------------------

    def _on_card_clicked(self, mode_id: str) -> None:
        if self._is_launching:
            return
        self._is_launching = True
        self._launch_message = ""

        self._beam_card = self._mode_cards.get(mode_id)
        self._beam_t = 0.0
        self._beam_active = True

        self._status_label.setText(
            f"MODO {mode_id.upper()} SELECCIONADO - INICIANDO..."
        )

        color = self._config.get("modes", {}).get(mode_id, {}).get("color", "#00FFFF")
        flash = FlashOverlay(color, self)
        flash.show()
        flash.raise_()
        self._flash_anim = flash.animate()

        if self._on_mode_selected:
            self._on_mode_selected(mode_id)

        # Opcion C del diseno: al elegir un modo el launcher se oculta y
        # deja al frente las aplicaciones lanzadas. Se vuelve con el atajo
        # global (Ctrl+Shift+Espacio) o desde la bandeja.
        QTimer.singleShot(700, self.hide)

    def set_launch_complete(
        self,
        mode_id: str,
        mode_name: str,
        launched: list[str],
        failed: list[str],
    ) -> None:
        self._is_launching = False
        self._beam_active = False
        self._beam_card = None
        self._state.record_mode(mode_id, mode_name)

        if failed:
            self._launch_message = (
                f"{mode_name} COMPLETADO: {len(launched)} apps abiertas, "
                f"{len(failed)} fallaron"
            )
            self._status_label.setText(self._launch_message)
            notify(
                "J.A.R.V.I.S.",
                f"{mode_name}: {len(launched)} apps abiertas, "
                f"{len(failed)} fallaron.",
            )
        else:
            self._launch_message = (
                f"{mode_name} COMPLETADO: {len(launched)} apps abiertas"
            )
            self._status_label.setText(self._launch_message)
            notify(
                "J.A.R.V.I.S.",
                f"{mode_name} listo: {len(launched)} apps abiertas.",
            )

    # ------------------------------------------------------------------
    # Auto-inicio
    # ------------------------------------------------------------------

    def _toggle_startup(self) -> None:
        startup_dir = os.path.join(
            os.environ["APPDATA"],
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        vbs_path = os.path.join(startup_dir, "JarvisLauncher.vbs")
        bat_path = os.path.join(startup_dir, "JarvisLauncher.bat")

        if os.path.exists(vbs_path) or os.path.exists(bat_path):
            for p_ in [vbs_path, bat_path]:
                if os.path.exists(p_):
                    os.remove(p_)
            self._status_label.setText("AUTO-INICIO DESACTIVADO")
            self._setup_btn.setText("Configurar auto-inicio")
        else:
            main_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "main.py",
            )
            python_exe = sys.executable
            vbs_content = (
                f'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{python_exe}"" ""{main_script}""", 0, False\n'
            )
            try:
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_content)
                self._status_label.setText("AUTO-INICIO ACTIVADO")
                self._setup_btn.setText("Desactivar auto-inicio")
            except PermissionError:
                self._status_label.setText(
                    "PERMISOS INSUFICIENTES - EJECUTA COMO ADMIN"
                )

    # ------------------------------------------------------------------
    # Timer principal
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        for i in range(len(self._ring_angles)):
            self._ring_angles[i] += self.RING_SPEEDS[i]
            if self._ring_angles[i] >= 360:
                self._ring_angles[i] -= 360

        for p_ in self._particles:
            p_.canvas_w = self.width()
            p_.canvas_h = self.height()
            p_.update()

        self._scan_y += 1.5
        if self._scan_y > self.height() + 20:
            self._scan_y = -20

        if self._beam_active:
            self._beam_t += 0.016
            if self._beam_t > 1.2:
                self._beam_t = 0.0

        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        them = self._theme.theme

        # Fondo del tema (degradado sutil)
        bg = QColor(them.bg)
        p.fillRect(0, 0, w, h, bg)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(them.bg))
        grad.setColorAt(1.0, QColor(them.bg_alt).darker(int(100 * 0.64))
                        if False else QColor(them.bg_alt))
        p.fillRect(0, 0, w, h, bg)

        # Grid sutil
        self._draw_grid(p, w, h, them.grid, them.text_dim)
        # Particulas
        self._draw_particles(p)
        # Anillos HUD
        self._draw_hud_rings(p, w, h, them)
        # Scan line
        self._draw_scan_line(p, w, them.scan)
        # Beam
        self._draw_beam(p, w, h, them)
        # Vignette
        self._draw_vignette(p, w, h, them.bg_alt)

    # ------------------------------------------------------------------
    # Dibujos de fondo
    # ------------------------------------------------------------------

    def _draw_grid(self, p: QPainter, w: int, h: int, accent: str, dim: str) -> None:
        grid_pen = QPen(ThemeManager.rgba(accent, 12))
        grid_pen.setWidth(1)
        p.setPen(grid_pen)
        spacing = 60
        for x in range(0, w, spacing):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, spacing):
            p.drawLine(0, y, w, y)

    def _draw_particles(self, p: QPainter) -> None:
        for particle in self._particles:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(particle.color)
            p.drawEllipse(
                int(particle.x), int(particle.y),
                int(particle.size), int(particle.size),
            )

    def _draw_hud_rings(self, p: QPainter, w: int, h: int, them) -> None:
        cx, cy = w // 2, h // 2
        base_radius = min(w, h) * self.HUD_RING_RADIUS_RATIO
        ring_colors = [them.ring_outer, them.ring_mid, them.ring_inner]
        ring_configs = [
            (base_radius, 80, self.RING_SPEEDS[0]),
            (base_radius * 0.72, 60, self.RING_SPEEDS[1]),
            (base_radius * 0.45, 40, self.RING_SPEEDS[2]),
        ]
        for idx, (radius, _, _) in enumerate(ring_configs):
            col = QColor(ring_colors[idx])
            angle = self._ring_angles[idx]
            alpha_base = [25, 35, 45][idx]
            pen = QPen(QColor(col.red(), col.green(), col.blue(), alpha_base))
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([12.0, 8.0 + idx * 4.0])
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.save()
            p.translate(cx, cy)
            p.rotate(angle)
            p.drawEllipse(int(-radius), int(-radius), int(radius * 2), int(radius * 2))
            p.restore()
            self._draw_ring_ticks(
                p, cx, cy, radius, col.red(), col.green(), col.blue(), alpha_base
            )
        self._draw_center_core(p, cx, cy, base_radius, them)

    def _draw_ring_ticks(
        self, p: QPainter, cx: int, cy: int, radius: float, r: int, g: int, b: int, alpha: int
    ) -> None:
        tick_pen = QPen(QColor(r, g, b, alpha + 15))
        tick_pen.setWidth(1)
        p.setPen(tick_pen)
        num_ticks = 36
        inner = radius - 5
        outer = radius + 5
        for i in range(num_ticks):
            angle_rad = math.radians(i * (360 / num_ticks))
            x1 = cx + inner * math.cos(angle_rad)
            y1 = cy + inner * math.sin(angle_rad)
            x2 = cx + outer * math.cos(angle_rad)
            y2 = cy + outer * math.sin(angle_rad)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_center_core(self, p: QPainter, cx: int, cy: int, base_radius: float, them) -> None:
        core_radius = base_radius * 0.15
        glow_r = core_radius * 3
        col = QColor(them.ring_inner)
        grad = QRadialGradient(float(cx), float(cy), glow_r)
        grad.setColorAt(0.0, QColor(col.red(), col.green(), col.blue(), 25))
        grad.setColorAt(0.5, QColor(col.red(), col.green(), col.blue(), 8))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawEllipse(int(cx - glow_r), int(cy - glow_r), int(glow_r * 2), int(glow_r * 2))

        core_pen = QPen(QColor(col.red(), col.green(), col.blue(), 80))
        core_pen.setWidth(2)
        p.setPen(core_pen)
        p.setBrush(QColor(col.red(), col.green(), col.blue(), 15))
        p.drawEllipse(
            int(cx - core_radius), int(cy - core_radius),
            int(core_radius * 2), int(core_radius * 2),
        )

    def _draw_scan_line(self, p: QPainter, w: int, accent: str) -> None:
        y = int(self._scan_y)
        col = QColor(accent)
        grad = QLinearGradient(0, y - 10, 0, y + 10)
        grad.setColorAt(0.0, QColor(col.red(), col.green(), col.blue(), 0))
        grad.setColorAt(0.5, QColor(col.red(), col.green(), col.blue(), 30))
        grad.setColorAt(1.0, QColor(col.red(), col.green(), col.blue(), 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRect(0, y - 10, w, 20)

    def _draw_vignette(self, p: QPainter, w: int, h: int, accent: str) -> None:
        cx, cy = w // 2, h // 2
        max_r = math.sqrt(cx * cx + cy * cy)
        grad = QRadialGradient(float(cx), float(cy), max_r)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.72, QColor(0, 0, 0, 0))
        diff = 1 if self._theme.theme.is_dark else 0
        grad.setColorAt(1.0, QColor(0, 0, 0, 120 if diff else 55))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRect(0, 0, w, h)

    def _draw_beam(self, p: QPainter, w: int, h: int, them) -> None:
        if not self._beam_active or self._beam_card is None:
            return
        if not self._beam_card.isVisible():
            return
        cx, cy = w // 2, h // 2
        target = self._beam_card.mapTo(self, self._beam_card.rect().center())
        pulse = 0.6 + 0.4 * math.sin(self._beam_t * 14.0)
        alpha = int(90 * pulse)
        col = QColor(them.accent)
        dx = target.x() - cx
        dy = target.y() - cy
        dist = math.hypot(dx, dy)
        if dist < 20:
            return
        travel = self._beam_t % 1.0
        px = cx + dx * travel
        py = cy + dy * travel
        beam_pen = QPen(QColor(col.red(), col.green(), col.blue(), alpha))
        beam_pen.setWidth(2)
        p.setPen(beam_pen)
        p.drawLine(cx, cy, int(px), int(py))
        grad = QRadialGradient(float(target.x()), float(target.y()), 60)
        grad.setColorAt(0.0, QColor(col.red(), col.green(), col.blue(), int(90 * pulse)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawEllipse(target.x() - 60, target.y() - 60, 120, 120)

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:
        # Si el lector esta abierto, sus atajos tienen prioridad
        if self._news_reader is not None and self._news_reader.isVisible():
            if self._news_reader.handle_key(event):
                return
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                self._center_on_screen()
            else:
                self.showFullScreen()
        super().keyPressEvent(event)