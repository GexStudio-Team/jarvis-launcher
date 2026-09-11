"""
ui/mode_card.py - Tarjeta de modo (Gaming / Trabajo / Estudio) estilo workspace.

Rediseno v2 (modo workspace / focus mode):
  - Estetica profesional sobria: monograma tipografico en lugar del icono
    emoji flotante, barra de acento superior estilo IDE y paleta de tema
    (sin exceso de neones ni brackets HUD).
  - Jerarquia clara: titulo del modo, descripcion breve y contador de
    aplicaciones en tipografia de terminal.
  - Los MODOS se conservan (Gaming/Trabajo/Estudio) tal como pidio el
    usuario; solo cambia la presentacion visual a un tono pro/workspace.

Propiedades animables (QPropertyAnimation):
  - glowOpacity (halo hover)
  - cardHeight  (pulse al click)
  - entrance    (fade+slide de aparicion)
  - sweep       (progreso 0..1 del barrido al seleccionar)
  - zoom        (escala visual al hover, pintura escalada)
  - iconFloat   (offset vertical del monograma, loop con QTimer)
"""

from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
    pyqtProperty,
    pyqtSignal,
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
from PyQt6.QtWidgets import QWidget

from core.themes import ThemeManager


class ModeCard(QWidget):
    """Tarjeta visual de un modo de operacion, totalmente custom-painted."""

    HOVER_HEIGHT_BOOST = 10
    ICON_FLOAT_AMP = 5.0     # px de flotacion (arriba/abajo)
    ICON_FLOAT_SPEED = 2.4   # rad/s

    # Senal emitida al hacer click izquierdo
    modeClicked = pyqtSignal(str)

    def __init__(
        self,
        mode_id: str,
        name: str,
        icon: str,
        color: str,
        description: str,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.mode_id = mode_id
        self._name = name
        self._icon = icon
        self._color = QColor(color)
        self._description = description
        self._theme = theme

        # Estado visual
        self._is_hovered = False
        self._glow_opacity: float = 0.0
        self._entrance: float = 1.0
        self._sweep: float = 0.0
        self._zoom: float = 1.0
        self._icon_float: float = 0.0
        self._float_t: float = 0.0
        self._app_count: int = 0
        self._base_height: int = 235
        self._current_height: int = self._base_height

        self.setFixedSize(290, self._base_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        # Loop de flotacion del icono (~30fps)
        self._float_timer = QTimer(self)
        self._float_timer.timeout.connect(self._tick_float)
        self._float_timer.start(33)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def set_app_count(self, count: int) -> None:
        self._app_count = count
        self.update()

    # ------------------------------------------------------------------
    # Animacion de entrada (escalonada desde el layout padre)
    # ------------------------------------------------------------------

    def play_entrance(self, delay_ms: int = 0, duration: int = 520) -> None:
        """Fade-in + slide up de la card (se llama con delay distinto por card)."""
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, lambda: self._run_entrance(duration))
        else:
            self._run_entrance(duration)

    def _run_entrance(self, duration: int) -> None:
        self._entrance = 0.0
        anim = QPropertyAnimation(self, b"entrance")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._entrance_anim = anim

    def _tick_float(self) -> None:
        self._float_t += 0.033
        self._icon_float = (
            self.ICON_FLOAT_AMP * 0.5
            * (1.0 + 0.4 * __import__("math").sin(self._float_t * self.ICON_FLOAT_SPEED))
        )
        self.update()

    # ------------------------------------------------------------------
    # Interaccion
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.animate_press()
            self.play_sweep()
            self.modeClicked.emit(self.mode_id)
        super().mousePressEvent(event)

    def animate_press(self) -> None:
        """Pulso rapido (alto -> bajo -> alto)."""
        group = QSequentialAnimationGroup(self)
        down = QPropertyAnimation(self, b"cardHeight")
        down.setDuration(80)
        down.setStartValue(self._current_height)
        down.setEndValue(self._base_height - 8)
        down.setEasingCurve(QEasingCurve.Type.OutQuad)
        up = QPropertyAnimation(self, b"cardHeight")
        up.setDuration(90)
        up.setStartValue(self._base_height - 8)
        up.setEndValue(self._base_height)
        up.setEasingCurve(QEasingCurve.Type.InOutQuad)
        group.addAnimation(down)
        group.addAnimation(up)
        group.start(QSequentialAnimationGroup.DeletionPolicy.DeleteWhenStopped)

    def play_sweep(self, duration: int = 650) -> None:
        """Barrido de energia horizontal superior al seleccionar."""
        self._sweep = 0.0
        anim = QPropertyAnimation(self, b"sweepProg")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._sweep_anim = anim

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        self._animate_glow(1.0)
        self._animate_height(self._base_height + self.HOVER_HEIGHT_BOOST)
        self._animate_zoom(1.02)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self._animate_glow(0.0)
        self._animate_height(self._base_height)
        self._animate_zoom(1.0)
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Animaciones helper
    # ------------------------------------------------------------------

    def _animate_glow(self, target: float) -> None:
        anim = QPropertyAnimation(self, b"glowOpacity")
        anim.setDuration(240)
        anim.setStartValue(self._glow_opacity)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._glow_anim = anim

    def _animate_height(self, target: int) -> None:
        anim = QPropertyAnimation(self, b"cardHeight")
        anim.setDuration(200)
        anim.setStartValue(self._current_height)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._height_anim = anim

    def _animate_zoom(self, target: float) -> None:
        anim = QPropertyAnimation(self, b"zoomScale")
        anim.setDuration(200)
        anim.setStartValue(self._zoom)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()
        self._zoom_anim = anim

    # ------------------------------------------------------------------
    # Qt Properties
    # ------------------------------------------------------------------

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

    def _get_entrance(self) -> float:
        return self._entrance

    def _set_entrance(self, val: float) -> None:
        self._entrance = val
        self.update()

    entrance = pyqtProperty(float, _get_entrance, _set_entrance)

    def _get_sweep(self) -> float:
        return self._sweep

    def _set_sweep(self, val: float) -> None:
        self._sweep = val
        self.update()

    sweepProg = pyqtProperty(float, _get_sweep, _set_sweep)

    def _get_zoom(self) -> float:
        return self._zoom

    def _set_zoom(self, val: float) -> None:
        self._zoom = val
        self.update()

    zoomScale = pyqtProperty(float, _get_zoom, _set_zoom)

    # ------------------------------------------------------------------
    # Pintura
    # ------------------------------------------------------------------

    @staticmethod
    def _rounded_rect_path(w: float, h: float, radius: float) -> QPainterPath:
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
        return path

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        them = self._theme.theme
        radius = 16.0

        # Entrance: fade + slide up
        e = max(0.0, min(1.0, self._entrance))
        if e <= 0.01:
            p.end()
            return
        slide_up = int((1.0 - e) * 26)
        p.translate(0, slide_up)
        h_eff = h - slide_up

        # Glow alpha combinado (hover * entrance)
        glow = self._glow_opacity * e
        alpha_scale = e

        # ---- Zoom al hover (escala centrada) ----
        if abs(self._zoom - 1.0) > 0.001:
            cx, cy = w / 2, (h_eff + slide_up) / 2
            p.translate(cx, cy)
            p.scale(self._zoom, self._zoom)
            p.translate(-cx, -cy)

        # ---- Halo exterior sutil (hover) ----
        if glow > 0.01:
            p.save()
            halo_path = self._rounded_rect_path(w + 30, h_eff + 30, radius + 9)
            halo_path.translate(-15, -15)
            halo_grad = QRadialGradient(w / 2, h_eff / 2, w * 0.6)
            glow_color = QColor(self._color)
            glow_color.setAlpha(int(28 * glow))
            halo_grad.setColorAt(0.0, glow_color)
            halo_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(halo_grad)
            p.drawPath(halo_path)
            p.restore()

        # ---- Path principal ----
        path = self._rounded_rect_path(w, h_eff, radius)

        # ---- Fondo workspace (sobrio, segun tema) ----
        p.save()
        p.setClipPath(path)
        bg = QColor(them.card_bg)
        bg.setAlpha(int(225 * alpha_scale))
        p.fillRect(0, 0, w, h_eff, bg)
        p.restore()

        # ---- Borde neutro + acento del modo al hover ----
        p.save()
        border_alpha = int((70 + 90 * glow) * alpha_scale)
        border_col = QColor(self._color)
        border_col.setAlpha(border_alpha)
        border_pen = QPen(border_col)
        border_pen.setWidth(1)
        p.setPen(border_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.restore()

        # ---- Glow radial interior (hover, muy sutil) ----
        if glow > 0.01:
            p.save()
            p.setClipPath(path)
            inner_grad = QRadialGradient(w / 2, h_eff / 3, h_eff * 0.85)
            inner_color = QColor(self._color)
            inner_color.setAlpha(int(34 * glow))
            inner_grad.setColorAt(0.0, inner_color)
            inner_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillRect(0, 0, w, h_eff, inner_grad)
            p.restore()

        # ---- Barrido de energia (sweep) ----
        if self._sweep > 0.0 and self._sweep < 1.0:
            self._draw_sweep(p, w, h_eff, radius)

        # ---- Barra de acento superior tipo IDE ----
        self._draw_accent_bar(p, w, e, glow)

        # ---- Monograma + texto (workspace) ----
        self._draw_content(p, w, h_eff, e)

        # ---- Linea decorativa inferior sutil ----
        p.save()
        p.setClipPath(path)
        line_pen = QPen(
            QColor(
                self._color.red(),
                self._color.green(),
                self._color.blue(),
                int((40 + 26 * glow) * alpha_scale),
            )
        )
        line_pen.setWidth(1)
        p.setPen(line_pen)
        p.drawLine(24, h_eff - 44, w - 24, h_eff - 44)
        p.restore()

        p.end()

    def _draw_sweep(self, p: QPainter, w: int, h: int, radius: float) -> None:
        """Barrido horizontal estilo radar que cruza la card al seleccionar."""
        x = self._sweep * (w + 60) - 30
        grad = QLinearGradient(x - 14, 0, x + 14, 0)
        sweep_c = QColor(self._color)
        sweep_c.setAlpha(200)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.5, sweep_c)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.save()
        p.setClipPath(self._rounded_rect_path(w, h, radius))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRect(int(x - 14), 0, 28, h)
        p.restore()

    def _draw_content(self, p: QPainter, w: int, h: int, e: float) -> None:
        """Monograma sobrio + nombre, descripcion y contador (modo workspace).

        A diferencia de la v1.4 (icono emoji flotante), el modo workspace usa
        un monograma disciplinado: las iniciales del modo en un contenedor
        redondeado con el color de acento, jerarquia clara y sin ruido.
        """
        them = self._theme.theme

        # ---- Monograma (inicial del modo) ----
        mono_size = 58
        mono_y = int(h * 0.20) + int(self._icon_float)
        mono_rect = (
            w // 2 - mono_size // 2,
            mono_y - mono_size // 2,
            mono_size,
            mono_size,
        )

        # Contenedor redondeado sobrio
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        container_path = QPainterPath()
        container_path.addRoundedRect(
            mono_rect[0], mono_rect[1], mono_rect[2], mono_rect[3], 12, 12
        )
        fill = QColor(self._color)
        fill.setAlpha(int(26 * e))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(fill)
        p.drawPath(container_path)
        border_col = QColor(self._color)
        border_col.setAlpha(int(90 * e))
        border_pen = QPen(border_col)
        border_pen.setWidth(1)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(border_pen)
        p.drawPath(container_path)
        p.restore()

        # Inicial del modo (sin emoji)
        initial = (self._name or "?").strip()[:1].upper()
        mono_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        mono_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(mono_font)
        mono_col = QColor(self._color)
        mono_col.setAlpha(int(225 * e))
        p.setPen(mono_col)
        p.drawText(
            mono_rect[0],
            mono_rect[1],
            mono_rect[2],
            mono_rect[3],
            Qt.AlignmentFlag.AlignCenter,
            initial,
        )

        # ---- Nombre del modo ----
        name_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        name_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        p.setFont(name_font)
        name_color = QColor(them.text)
        name_color.setAlpha(int(235 * e))
        p.setPen(name_color)
        p.drawText(
            0,
            int(h * 0.46),
            w,
            int(h * 0.12),
            Qt.AlignmentFlag.AlignHCenter,
            self._name,
        )

        # ---- Descripcion ----
        if self._description:
            desc_font = QFont("Segoe UI", 10)
            p.setFont(desc_font)
            desc_color = QColor(them.text_dim)
            desc_color.setAlpha(int(200 * e))
            p.setPen(desc_color)
            p.drawText(
                16,
                int(h * 0.58),
                w - 32,
                int(h * 0.18),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self._description,
            )

        # ---- Contador de apps (tipo status bar) ----
        word = "aplicacion" if self._app_count == 1 else "aplicaciones"
        count_text = f"{self._app_count} {word}"
        count_font = QFont("Consolas", 9)
        p.setFont(count_font)
        count_color = QColor(them.text_dim)
        count_color.setAlpha(int(160 * e))
        p.setPen(count_color)
        p.drawText(
            0,
            int(h * 0.82),
            w,
            int(h * 0.1),
            Qt.AlignmentFlag.AlignHCenter,
            count_text,
        )

    def _draw_accent_bar(self, p: QPainter, w: int, e: float, glow: float) -> None:
        """Barra de acento superior estilo IDE (sobria, plena al hover)."""
        bar_h = 3
        bar_w = int(w * (0.42 + 0.5 * glow))
        x0 = (w - bar_w) // 2
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        accent = QColor(self._color)
        accent.setAlpha(int(170 * e))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(accent)
        p.drawRoundedRect(x0, 0, bar_w, bar_h, 2, 2)
        p.restore()