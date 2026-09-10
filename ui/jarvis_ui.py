"""
ui/jarvis_ui.py - Ventana principal del Jarvis Launcher.

Efectos visuales:
  - Fondo oscuro con anillos HUD concentricos rotantes
  - Particulas flotantes
  - Linea de escaneo horizontal
  - Grid sutil de fondo
  - Texto con efecto glow
  - Pantalla de boot animada con barra de progreso (100% custom paint)
  - Greeting con efecto typewriter
  - Flash de color del modo al seleccionar
  - Beam de energia desde el nucleo hacia la card seleccionada
  - Transiciones suaves entre estados

IMPORTANTE: no se usan QGraphicsEffect (QGraphicsOpacityEffect / 
QGraphicsDropShadowEffect). En Qt6, aplicarlos junto a paintEvent custom
produce conflictos de QPainter ("paint device already painted"). Todos los
efectos de opacidad se hacen con propiedades propias + repintado manual, y
el fade de la ventana con la propiedad nativa windowOpacity.
"""

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
    QBrush,
    QPainter,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from core.feedback import play_click, play_success, play_error
from core.notifier import notify
from core.state import StateManager
from ui.mode_card import ModeCard


# ======================================================================
# Clases de efectos de fondo
# ======================================================================


class Particle:
    """Particula flotante animada en el fondo."""

    def __init__(self, width: int, height: int) -> None:
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.size = random.uniform(1.0, 3.0)
        self.speed_x = random.uniform(-0.3, 0.3)
        self.speed_y = random.uniform(-0.5, -0.1)
        self.opacity = random.uniform(30, 120)
        self.color = QColor(0, 255, 255, int(self.opacity))
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
# Overlays (boot y flash)
# ======================================================================


class BootOverlay(QWidget):
    """
    Pantalla de carga inicial tipo arranque de sistema.

    Pintura 100% custom (sin QGraphicsEffect): fondo oscuro, titulo con
    glow, barra de progreso animada, status con puntos y fecha.
    La propiedad `fade` (0..1) controla la opacidad total para el fade-out.
    """

    def __init__(self, app_name: str, version: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._app_name = app_name
        self._version = version
        self._fade: float = 1.0
        self._progress: float = 0.0
        self._dots = 0

        # Timer de animacion
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(32)

        # Timer de puntos
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_dots)
        self._dots_timer.start(220)

    # ------------------------------------------------------------------
    # Animaciones internas
    # ------------------------------------------------------------------

    def _tick_anim(self) -> None:
        # La barra de progreso avanza hasta 0.95 y luego espera el fade
        if self._progress < 0.95:
            self._progress = min(0.95, self._progress + 0.012)
        self.update()

    def _animate_dots(self) -> None:
        self._dots = (self._dots + 1) % 4
        self.update()

    def fade_out(self, on_done=None) -> None:
        """Animacion de salida del overlay (fade custom)."""
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

    # ------------------------------------------------------------------
    # Qt Property `fade`
    # ------------------------------------------------------------------

    def _get_fade(self) -> float:
        return self._fade

    def _set_fade(self, val: float) -> None:
        self._fade = val
        self.update()

    fade = pyqtProperty(float, _get_fade, _set_fade)

    # ------------------------------------------------------------------
    # Pintura
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        f = self._fade

        # Fondo solido
        p.fillRect(0, 0, w, h, QColor(8, 10, 18, int(255 * f)))

        # Titulo con glow (doblete de texto para efecto neon)
        title_font = QFont("Segoe UI", 40, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 10)
        p.setFont(title_font)

        # Medir el texto para centrarlo
        fm = p.fontMetrics()
        title_w = fm.horizontalAdvance(self._app_name)
        title_h = fm.height()
        title_x = (w - title_w) // 2
        title_y = h // 2 - 50

        # Sombra glow
        glow = QRadialGradient(
            float(w / 2), float(title_y + title_h / 2), float(title_w * 0.6)
        )
        glow.setColorAt(0.0, QColor(0, 255, 255, int(70 * f)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawRoundedRect(
            title_x - 60, title_y - 40, title_w + 120, title_h + 80, 40, 40
        )

        # Texto principal con glow simple
        p.setPen(QColor(0, 255, 255, int(235 * f)))
        p.drawText(title_x, title_y + title_h - 10, self._app_name)
        p.setPen(QColor(0, 255, 255, int(60 * f)))
        p.drawText(title_x + 2, title_y + title_h - 8, self._app_name)

        # Version
        p.setPen(QColor(255, 255, 255, int(80 * f)))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(w // 2 - 60, title_y + title_h + 10, f"v{self._version}")

        # Barra de progreso
        bar_w, bar_h = 340, 4
        bx = (w - bar_w) // 2
        by = title_y + title_h + 40
        p.setPen(QPen(QColor(0, 255, 255, int(50 * f)), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(bx, by, bar_w, bar_h, 2, 2)

        p.setPen(Qt.PenStyle.NoPen)
        filled = int(bar_w * self._progress)
        if filled > 4:
            grad = QLinearGradient(bx, by, bx + bar_w, by)
            grad.setColorAt(0.0, QColor(0, 180, 220, int(220 * f)))
            grad.setColorAt(1.0, QColor(0, 255, 255, int(220 * f)))
            p.setBrush(grad)
            p.drawRoundedRect(bx, by, filled, bar_h, 2, 2)

        # Status con puntos animados
        p.setPen(QColor(0, 255, 255, int(150 * f)))
        p.setFont(QFont("Segoe UI", 12))
        status = "INICIANDO SISTEMA" + "." * self._dots
        p.drawText(w // 2 - 80, by + 30, status)

        # Fecha
        p.setPen(QColor(255, 255, 255, int(70 * f)))
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

    # ------------------------------------------------------------------
    # Qt Property `alpha`
    # ------------------------------------------------------------------

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
        """Flash 0 -> 0.25 -> 0 y eliminacion del widget."""
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
# Widget principal JARVIS
# ======================================================================


class JarvisUI(QWidget):
    """Ventana fullscreen tipo Jarvis con todos los efectos HUD."""

    BG_COLOR = QColor(8, 10, 18)

    # Colores de anillos (de exterior a interior)
    RING_COLORS = [
        (0, 100, 180),   # azul oscuro
        (0, 180, 220),   # cyan
        (0, 255, 255),   # cyan brillante
    ]

    RING_SPEEDS = [0.3, -0.5, 0.8]  # grados por tick

    BOOT_DURATION_MS = 1900   # duracion de la pantalla de boot
    TYPEWRITER_MS = 18        # intervalo de "tecleo" del greeting

    def __init__(self, config: dict, on_mode_selected=None) -> None:
        super().__init__()
        self._config = config
        self._on_mode_selected = on_mode_selected

        # Estado
        self._ring_angles = [0.0, 45.0, 90.0]
        self._particles: list[Particle] = []
        self._scan_y: float = 0.0
        self._title_opacity: float = 0.0
        self._cards_opacity: float = 0.0
        self._is_launching = False
        self._launch_message = ""

        # Beam de energia (card seleccionada animada)
        self._beam_card: ModeCard | None = None
        self._beam_t: float = 0.0
        self._beam_active = False

        # Estado de ultimos modos
        self._state = StateManager()

        # Setup ventana
        self.setWindowTitle("J.A.R.V.I.S. Launcher")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumSize(1200, 800)
        self._center_on_screen()

        # Timer de animacion (~60fps)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        # Inicializar particulas
        self._init_particles(80)

        # Construir UI
        self._build_ui()

        # Secuencia de arranque
        self._run_boot_sequence()

    # ------------------------------------------------------------------
    # Inicializacion
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """
        Centra la ventana en el monitor principal usando
        availableGeometry (PyQt6 - no usa QDesktopWidget).
        Soporta multi-monitor (centra en el primario).
        """
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        w = min(1400, geo.width() - 80)
        h = min(900, geo.height() - 80)
        x = geo.x() + (geo.width() - w) // 2
        y = geo.y() + (geo.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def _init_particles(self, count: int) -> None:
        w, h = self.width(), self.height()
        self._particles = [Particle(w, h) for _ in range(count)]

    # ------------------------------------------------------------------
    # UI Layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ---- Layout principal ----
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(60, 40, 60, 30)
        self._main_layout.setSpacing(0)

        # ---- Barra superior (logo + setup) ----
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 20)

        logo_label = QLabel("J.A.R.V.I.S.", self)
        logo_label.setStyleSheet(
            """
            QLabel {
                color: #00FFFF;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 4px;
            }
            """
        )
        top_bar.addWidget(logo_label)
        top_bar.addStretch()

        self._setup_btn = QPushButton("Configurar auto-inicio", self)
        self._setup_btn.setFixedHeight(36)
        self._setup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(0, 255, 255, 15);
                color: rgba(0, 255, 255, 160);
                border: 1px solid rgba(0, 255, 255, 40);
                border-radius: 8px;
                padding: 0 16px;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(0, 255, 255, 30);
                color: #00FFFF;
                border-color: rgba(0, 255, 255, 80);
            }
            """
        )
        self._setup_btn.clicked.connect(self._toggle_startup)
        top_bar.addWidget(self._setup_btn)

        close_btn = QPushButton("X", self)
        close_btn.setFixedSize(36, 36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 100);
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF4444;
            }
            """
        )
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)

        self._main_layout.addLayout(top_bar)

        # ---- Espaciador superior ----
        self._main_layout.addSpacing(20)

        # ---- Titulo principal ----
        self._title_container = QWidget(self)
        title_layout = QVBoxLayout(self._title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._greeting_label = QLabel("", self)
        self._greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._greeting_label.setWordWrap(True)
        self._greeting_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 200);
                font-size: 20px;
                font-weight: 300;
                letter-spacing: 1px;
            }
            """
        )
        title_layout.addWidget(self._greeting_label)

        self._main_layout.addWidget(self._title_container)
        self._main_layout.addSpacing(30)

        # ---- Cards container ----
        self._cards_container = QWidget(self)
        self._cards_layout = QHBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(30)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._mode_cards: dict[str, ModeCard] = {}
        self._create_mode_cards()

        self._main_layout.addWidget(
            self._cards_container, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # ---- Espaciador inferior ----
        self._main_layout.addStretch()

        # ---- Status bar ----
        self._status_bar = QHBoxLayout()
        self._status_bar.setContentsMargins(0, 10, 0, 0)

        self._status_label = QLabel("SISTEMA LISTO", self)
        self._status_label.setStyleSheet(
            """
            QLabel {
                color: rgba(0, 255, 255, 120);
                font-size: 10px;
                letter-spacing: 3px;
            }
            """
        )
        self._status_bar.addWidget(self._status_label)
        self._status_bar.addStretch()

        version_label = QLabel(
            f"v{self._config.get('version', '1.0.0')}", self
        )
        version_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 50);
                font-size: 10px;
            }
            """
        )
        self._status_bar.addWidget(version_label)
        self._main_layout.addLayout(self._status_bar)

    def _create_mode_cards(self) -> None:
        """Crea las tarjetas de modo desde la configuracion."""
        modes = self._config.get("modes", {})
        for mode_id, mode_data in modes.items():
            card = ModeCard(
                mode_id=mode_id,
                name=mode_data.get("name", mode_id),
                icon=mode_data.get("icon", "?"),
                color=mode_data.get("color", "#00FFFF"),
                description=mode_data.get("description", ""),
                parent=self,
            )
            apps = mode_data.get("apps", [])
            card.set_app_count(len(apps))
            card.modeClicked.connect(self._on_card_clicked)
            self._mode_cards[mode_id] = card
            self._cards_layout.addWidget(card)

    # ------------------------------------------------------------------
    # Secuencia de arranque (boot + typewriter)
    # ------------------------------------------------------------------

    def _run_boot_sequence(self) -> None:
        """Pantalla de boot, luego fade (windowOpacity) y typewriter."""
        # Fade-in de la ventana (propiedad nativa, sin QGraphicsEffect)
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(600)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start()
        self._fade_anim = fade

        # Overlay de boot
        self._boot_overlay = BootOverlay(
            app_name=self._config.get("app_name", "J.A.R.V.I.S."),
            version=self._config.get("version", "1.0.0"),
            parent=self,
        )
        self._boot_overlay.show()
        self._boot_overlay.raise_()

        QTimer.singleShot(
            self.BOOT_DURATION_MS,
            lambda: self._boot_overlay.fade_out(self._start_typewriter),
        )

    def _start_typewriter(self) -> None:
        """Anima el greeting caracter por caracter."""
        full_text = self._config.get(
            "greeting", "Selecciona tu modo de operacion:"
        )
        self._greeting_pos = 0

        self._type_timer = QTimer(self)
        self._type_timer.timeout.connect(self._type_char)
        self._type_timer.start(self.TYPEWRITER_MS)

        # Guard: si el greeting es corto, que se complete rapido
        self._full_greeting = full_text
        self._type_char()

        self._update_status_ready()

    def _type_char(self) -> None:
        self._greeting_pos += 2
        self._greeting_label.setText(self._full_greeting[: self._greeting_pos])
        if self._greeting_pos >= len(self._full_greeting):
            self._type_timer.stop()

    def _update_status_ready(self) -> None:
        """Muestra en la barra de estado el ultimo modo usado."""
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
        """Maneja el click en una tarjeta de modo."""
        if self._is_launching:
            return

        play_click()
        self._is_launching = True
        self._launch_message = ""

        # Beam de energia hacia la card seleccionada
        self._beam_card = self._mode_cards.get(mode_id)
        self._beam_t = 0.0
        self._beam_active = True

        self._status_label.setText(
            f"MODO {mode_id.upper()} SELECCIONADO - INICIANDO..."
        )

        # Flash de color del modo
        color = self._config.get("modes", {}).get(
            mode_id, {}
        ).get("color", "#00FFFF")
        flash = FlashOverlay(color, self)
        flash.show()
        flash.raise_()
        self._flash_anim = flash.animate()

        if self._on_mode_selected:
            self._on_mode_selected(mode_id)

    def set_launch_complete(
        self,
        mode_id: str,
        mode_name: str,
        launched: list[str],
        failed: list[str],
    ) -> None:
        """Callback cuando termina el lanzamiento de apps."""
        self._is_launching = False
        self._beam_active = False
        self._beam_card = None

        # Registrar en historial
        self._state.record_mode(mode_id, mode_name)

        if failed:
            self._launch_message = (
                f"{mode_name} COMPLETADO: {len(launched)} apps abiertas, "
                f"{len(failed)} fallaron"
            )
            self._status_label.setText(self._launch_message)
            play_error()
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
            play_success()
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
            # Remover
            for p in [vbs_path, bat_path]:
                if os.path.exists(p):
                    os.remove(p)
            self._status_label.setText("AUTO-INICIO DESACTIVADO")
            self._setup_btn.setText("Configurar auto-inicio")
        else:
            # Crear
            main_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "main.py",
            )
            python_exe = sys.executable

            # VBS para ocultar la ventana de consola
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
    # Timer de animacion (loop principal)
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        # Rotar anillos
        for i in range(len(self._ring_angles)):
            self._ring_angles[i] += self.RING_SPEEDS[i]
            if self._ring_angles[i] >= 360:
                self._ring_angles[i] -= 360

        # Mover particulas
        for p in self._particles:
            p.canvas_w = self.width()
            p.canvas_h = self.height()
            p.update()

        # Scan line
        self._scan_y += 1.5
        if self._scan_y > self.height() + 20:
            self._scan_y = -20

        # Beam de energia
        if self._beam_active:
            self._beam_t += 0.016
            if self._beam_t > 1.2:
                self._beam_t = 0.0

        self.update()

    # ------------------------------------------------------------------
    # Pintura principal
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # ---- Fondo solido ----
        p.fillRect(0, 0, w, h, self.BG_COLOR)

        # ---- Grid sutil ----
        self._draw_grid(p, w, h)

        # ---- Particulas ----
        self._draw_particles(p)

        # ---- Anillos HUD ----
        self._draw_hud_rings(p, w, h)

        # ---- Linea de escaneo ----
        self._draw_scan_line(p, w)

        # ---- Beam de energia hacia la card ----
        self._draw_beam(p, w, h)

        # ---- Overlay radial oscuro (vignette) ----
        self._draw_vignette(p, w, h)

    def _draw_grid(self, p: QPainter, w: int, h: int) -> None:
        grid_pen = QPen(QColor(0, 255, 255, 8))
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
                int(particle.x),
                int(particle.y),
                int(particle.size),
                int(particle.size),
            )

    def _draw_hud_rings(self, p: QPainter, w: int, h: int) -> None:
        cx, cy = w // 2, h // 2
        base_radius = min(w, h) * 0.32
        ring_configs = [
            (base_radius, 80, self.RING_SPEEDS[0]),
            (base_radius * 0.72, 60, self.RING_SPEEDS[1]),
            (base_radius * 0.45, 40, self.RING_SPEEDS[2]),
        ]

        for idx, (radius, _, _) in enumerate(ring_configs):
            r, g, b = self.RING_COLORS[idx]
            angle = self._ring_angles[idx]
            alpha_base = [25, 35, 45][idx]

            # Anillo principal
            pen = QPen(QColor(r, g, b, alpha_base))
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.DashLine)
            dash_pattern = [12.0, 8.0 + idx * 4.0]
            pen.setDashPattern(dash_pattern)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)

            p.save()
            p.translate(cx, cy)
            p.rotate(angle)
            p.drawEllipse(
                int(-radius), int(-radius),
                int(radius * 2), int(radius * 2),
            )
            p.restore()

            # Marcas de graduacion (ticks)
            self._draw_ring_ticks(p, cx, cy, radius, r, g, b, alpha_base)

        # ---- Centro: circulo pulsante ----
        self._draw_center_core(p, cx, cy, base_radius)

    def _draw_ring_ticks(
        self,
        p: QPainter,
        cx: int,
        cy: int,
        radius: float,
        r: int,
        g: int,
        b: int,
        alpha: int,
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

    def _draw_center_core(
        self, p: QPainter, cx: int, cy: int, base_radius: float
    ) -> None:
        core_radius = base_radius * 0.15

        # Glow exterior
        glow_r = core_radius * 3
        grad = QRadialGradient(float(cx), float(cy), glow_r)
        grad.setColorAt(0.0, QColor(0, 255, 255, 25))
        grad.setColorAt(0.5, QColor(0, 255, 255, 8))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawEllipse(
            int(cx - glow_r), int(cy - glow_r),
            int(glow_r * 2), int(glow_r * 2),
        )

        # Circulo central solido
        core_pen = QPen(QColor(0, 255, 255, 80))
        core_pen.setWidth(2)
        p.setPen(core_pen)
        p.setBrush(QColor(0, 255, 255, 15))
        p.drawEllipse(
            int(cx - core_radius), int(cy - core_radius),
            int(core_radius * 2), int(core_radius * 2),
        )

    def _draw_beam(self, p: QPainter, w: int, h: int) -> None:
        """
        Beam de energia desde el nucleo central hacia la card seleccionada.

        Se dibuja un cono/triangulo con gradiente que pulsa (via _beam_t).
        """
        if not self._beam_active or self._beam_card is None:
            return
        if not self._beam_card.isVisible():
            return

        cx, cy = w // 2, h // 2
        target = self._beam_card.mapTo(self, self._beam_card.rect().center())

        # Pulso sinusoidal
        pulse = 0.6 + 0.4 * math.sin(self._beam_t * 14.0)
        alpha = int(90 * pulse)

        # Cono desde el nucleo hacia la card
        dx = target.x() - cx
        dy = target.y() - cy
        dist = math.hypot(dx, dy)
        if dist < 20:
            return

        # Punto intermedio hacia donde viaja la energia
        travel = (self._beam_t % 1.0)
        px = cx + dx * travel
        py = cy + dy * travel

        # Linea principal
        beam_pen = QPen(QColor(0, 255, 255, alpha))
        beam_pen.setWidth(2)
        p.setPen(beam_pen)
        p.drawLine(cx, cy, int(px), int(py))

        # Halo alrededor de la card
        grad = QRadialGradient(float(target.x()), float(target.y()), 60)
        grad.setColorAt(0.0, QColor(0, 255, 255, int(90 * pulse)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawEllipse(target.x() - 60, target.y() - 60, 120, 120)

    def _draw_scan_line(self, p: QPainter, w: int) -> None:
        y = int(self._scan_y)
        grad = QLinearGradient(0, y - 10, 0, y + 10)
        grad.setColorAt(0.0, QColor(0, 255, 255, 0))
        grad.setColorAt(0.5, QColor(0, 255, 255, 30))
        grad.setColorAt(1.0, QColor(0, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRect(0, y - 10, w, 20)

    def _draw_vignette(self, p: QPainter, w: int, h: int) -> None:
        cx, cy = w // 2, h // 2
        max_r = math.sqrt(cx * cx + cy * cy)
        grad = QRadialGradient(float(cx), float(cy), max_r)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.6, QColor(0, 0, 0, 0))
        grad.setColorAt(1.0, QColor(0, 0, 0, 180))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRect(0, 0, w, h)

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                self._center_on_screen()
            else:
                self.showFullScreen()
        super().keyPressEvent(event)