"""
core/tray.py - Bandeja del sistema (QSystemTrayIcon).

El launcher vive todo el tiempo en la bandeja de Windows: al elegir un modo
se oculta en lugar de cerrarse, y el usuario lo vuelve a invocar con el atajo
global (Ctrl+Shift+Espacio) o desde el menu de la bandeja.

- Icono generado por codigo (QPainter) para no depender de assets externos.
- Menu contextual: Mostrar J.A.R.V.I.S. / Salir.
- Doble click en el icono -> muestra el launcher.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

logger = logging.getLogger("jarvis.tray")


def build_tray_icon(accent: str = "#00E5FF") -> QIcon:
    """Genera un icono de bandeja 'J' sobre circulo, estilo HUD, por codigo."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Circulo de fondo
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#0A0E14"))
    p.drawEllipse(2, 2, 60, 60)
    # Anillo
    ring = QColor(accent)
    p.setBrush(Qt.BrushStyle.NoBrush)
    pp = p.pen()
    pp.setColor(ring)
    pp.setWidth(3)
    p.setPen(pp)
    p.drawEllipse(6, 6, 52, 52)
    # Letra J
    from PyQt6.QtGui import QFont

    f = QFont("Segoe UI", 26, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor(accent))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "J")
    p.end()
    return QIcon(pm)


class Tray:
    """Encapsula la bandeja; delega las acciones al controlador."""

    def __init__(self, on_show, on_quit, accent: str = "#00E5FF") -> None:
        self._tray = QSystemTrayIcon(build_tray_icon(accent))
        self._tray.setToolTip("J.A.R.V.I.S. Launcher")
        self._on_show = on_show
        self._on_quit = on_quit

        menu = QMenu()
        show_action = QAction("Mostrar J.A.R.V.I.S.")
        show_action.triggered.connect(on_show)
        menu.addAction(show_action)

        quit_action = QAction("Salir")
        quit_action.triggered.connect(on_quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show()

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def is_visible(self) -> bool:
        return self._tray.isVisible()

    def show_message(self, title: str, message: str) -> None:
        try:
            self._tray.showMessage(title, message)
        except Exception:  # pragma: no cover - la bandeja no siempre esta lista
            logger.debug("Bandeja no disponible para mostrar mensaje.")

    def set_accent(self, accent: str) -> None:
        """Actualiza el color del icono al cambiar de tema."""
        self._tray.setIcon(build_tray_icon(accent))