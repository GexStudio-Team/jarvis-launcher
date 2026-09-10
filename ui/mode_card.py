"""
ui/mode_card.py - Tarjeta animada para cada modo del Jarvis Launcher.

Efectos: glassmorphism, hover con glow, borde animado, transiciones suaves.
"""

from PyQt6.QtCore import (
    Qt,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
    pyqtProperty,
    pyqtSignal,
    QSize,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QLinearGradient,
    QRadialGradient,
    QPen,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
)


class ModeCard(QWidget):
    """
    Tarjeta visual para un modo (Gaming / Trabajo / Estudio).

    Efectos:
      - Fondo glassmorphism semitransparente
      - Borde con gradiente del color del modo
      - Glow pulsante en hover
      - Animacion de elevacion al pasar el mouse
      - Icono grande, nombre y descripcion
    """

    HOVER_HEIGHT_BOOST = 8

    # Senal emitida al hacer click izquierdo
    modeClicked = pyqtSignal(str)

    def __init__(
        self,
        mode_id: str,
        name: str,
        icon: str,
        color: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.mode_id = mode_id
        self._name = name
        self._icon = icon
        self._color = QColor(color)
        self._description = description
        self._is_hovered = False
        self._glow_opacity: float = 0.0
        self._base_height: int = 220
        self._current_height: int = self._base_height

        self.setFixedSize(280, self._base_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        # Shadow
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setColor(QColor(0, 0, 0, 0))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)

        # Internal layout
        self._build_layout()

    # ------------------------------------------------------------------
    # Layout interno
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(8)

        # Icono
        self._icon_label = QLabel(self._icon, self)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        font = self._icon_label.font()
        font.setPixelSize(48)
        self._icon_label.setFont(font)

        # Nombre
        self._name_label = QLabel(self._name, self)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {self._color.name()};
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            """
        )

        # Descripcion
        self._desc_label = QLabel(self._description, self)
        self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 140);
                font-size: 12px;
            }
            """
        )

        # Apps count
        self._apps_label = QLabel("", self)
        self._apps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apps_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 80);
                font-size: 10px;
            }
            """
        )

        layout.addStretch()
        layout.addWidget(self._icon_label)
        layout.addWidget(self._name_label)
        layout.addWidget(self._desc_label)
        layout.addSpacing(4)
        layout.addWidget(self._apps_label)
        layout.addStretch()

    def set_app_count(self, count: int) -> None:
        word = "app" if count == 1 else "apps"
        self._apps_label.setText(f"{count} {word} para lanzar")

    # ------------------------------------------------------------------
    # Interaccion
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.animate_press()
            self.modeClicked.emit(self.mode_id)
        super().mousePressEvent(event)

    def animate_press(self) -> None:
        """Pulso rapido de presion (alto -> bajo -> alto)."""
        group = QSequentialAnimationGroup(self)

        down = QPropertyAnimation(self, b"cardHeight")
        down.setDuration(80)
        down.setStartValue(self._current_height)
        down.setEndValue(self._base_height - 6)
        down.setEasingCurve(QEasingCurve.Type.OutQuad)

        up = QPropertyAnimation(self, b"cardHeight")
        up.setDuration(90)
        up.setStartValue(self._base_height - 6)
        up.setEndValue(self._base_height)
        up.setEasingCurve(QEasingCurve.Type.InOutQuad)

        group.addAnimation(down)
        group.addAnimation(up)
        group.start(QSequentialAnimationGroup.DeletionPolicy.DeleteWhenStopped)

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        self._animate_glow(1.0)
        self._animate_shadow(True)
        self._animate_height(self._base_height + self.HOVER_HEIGHT_BOOST)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self._animate_glow(0.0)
        self._animate_shadow(False)
        self._animate_height(self._base_height)
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Animaciones
    # ------------------------------------------------------------------

    def _animate_glow(self, target: float) -> None:
        anim = QPropertyAnimation(self, b"glowOpacity")
        anim.setDuration(200)
        anim.setStartValue(self._glow_opacity)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._glow_anim = anim

    def _animate_shadow(self, active: bool) -> None:
        anim = QPropertyAnimation(self._shadow, b"blurRadius")
        anim.setDuration(250)
        if active:
            anim.setStartValue(0)
            anim.setEndValue(40)
            self._shadow.setColor(self._color)
        else:
            anim.setStartValue(40)
            anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._shadow_anim = anim

    def _animate_height(self, target: int) -> None:
        anim = QPropertyAnimation(self, b"cardHeight")
        anim.setDuration(200)
        anim.setStartValue(self._current_height)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._height_anim = anim

    # ---------------------------------------------------------------
    # Qt Properties para animaciones
    # ---------------------------------------------------------------

    def _get_glow(self) -> float:
        return self._glow_opacity

    def _set_glow(self, val: float) -> None:
        self._glow_opacity = val
        self.update()

    glowOpacity = pyqtProperty(float, _get_glow, _set_glow)

    def _get_height(self) -> int:
        return self._current_height

    def _set_height(self, val: int) -> None:
        self._current_height = val
        self.setFixedSize(self.width(), val)
        self.update()

    cardHeight = pyqtProperty(int, _get_height, _set_height)

    # ------------------------------------------------------------------
    # Pintura custom
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # ---- Path con esquinas redondeadas ----
        radius = 16.0
        path = QPainterPath()
        path.moveTo(radius, 0)
        path.lineTo(w - radius, 0)
        path.quadTo(w, 0, w, radius)
        path.lineTo(w, h - radius)
        path.quadTo(w, h, w - radius, h)
        path.lineTo(radius, h)
        path.quadTo(0, h, 0, h - radius)
        path.lineTo(0, radius)
        path.quadTo(0, 0, radius, 0)
        path.closeSubpath()

        # ---- Fondo glassmorphism ----
        p.save()
        p.setClipPath(path)
        bg = QColor(20, 20, 35, 200)
        p.fillRect(0, 0, w, h, bg)
        p.restore()

        # ---- Borde gradiente ----
        p.save()
        border_pen = QPen()
        border_pen.setWidth(2)
        border_grad = QLinearGradient(0, 0, w, h)
        alpha = int(80 + 175 * self._glow_opacity)
        border_grad.setColorAt(0.0, QColor(self._color.red(), self._color.green(), self._color.blue(), alpha))
        border_grad.setColorAt(1.0, QColor(self._color.red(), self._color.green(), self._color.blue(), int(alpha * 0.3)))
        border_pen.setBrush(border_grad)
        p.setPen(border_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.restore()

        # ---- Glow radial (hover) ----
        if self._glow_opacity > 0.01:
            p.save()
            p.setClipPath(path)
            center_x = w // 2
            center_y = h // 3
            glow_color = QColor(self._color)
            glow_color.setAlpha(int(60 * self._glow_opacity))
            grad = QRadialGradient(float(center_x), float(center_y), float(h * 0.8))
            grad.setColorAt(0.0, glow_color)
            grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillRect(0, 0, w, h, grad)
            p.restore()

        # ---- Linea decorativa inferior ----
        p.save()
        p.setClipPath(path)
        line_pen = QPen(QColor(self._color.red(), self._color.green(), self._color.blue(), int(60 + 40 * self._glow_opacity)))
        line_pen.setWidth(1)
        p.setPen(line_pen)
        p.drawLine(24, h - 40, w - 24, h - 40)
        p.restore()
