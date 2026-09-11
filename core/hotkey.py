"""
core/hotkey.py - Atajo global de Windows (RegisterHotKey + ctypes).

Registra una combinacion de teclas a nivel de sistema operativo y entrega
el evento a una llamada de Python cuando el usuario la pulsa desde cualquier
aplicacion (no solo cuando el launcher tiene el foco).

Implementacion con la API nativa de Windows:
  - RegisterHotKey(None, id, MOD_CONTROL | MOD_SHIFT, VK_SPACE) registra
    Ctrl+Shift+Espacio en el hilo de la aplicacion.
  - El mensaje WM_HOTKEY llega al bucle de Qt y se intercepta con un
    QAbstractNativeEventFilter.

Sin dependencias nuevas (cumple la politica del proyecto). Si otro programa
ya tiene registrado el mismo atajo, RegisterHotKey falla y el atajo simplemente
no se activa (degradacion silenciosa y logueada).
"""

from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

from PyQt6.QtCore import QAbstractNativeEventFilter

logger = logging.getLogger("jarvis.hotkey")

# Constantes de la API de Windows
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_SPACE = 0x20
WM_HOTKEY = 0x0312

HOTKEY_ID = 0x4A41  # 'J A' -> identificador unico para nuestra ventana


class Msg(ctypes.Structure):
    """Estructura MSG de Win32 (solo los campos que usamos)."""

    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


_user32 = ctypes.windll.user32

# Firmas explicitas para evitar truncado de punteros de 64 bits
_user32.RegisterHotKey.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
]
_user32.RegisterHotKey.restype = wintypes.BOOL
_user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.UnregisterHotKey.restype = wintypes.BOOL


class GlobalHotkey(QAbstractNativeEventFilter):
    """Registra Ctrl+Shift+Espacio y emite el callback al pulsarlo."""

    def __init__(self, on_triggered) -> None:
        super().__init__()
        self._on_triggered = on_triggered
        self._registered = False

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def register(self) -> bool:
        """
        Registra la combinacion global.

        Returns
        -------
        True si quedo registrado; False si otro proceso la tiene ocupada.
        """
        ok = bool(
            _user32.RegisterHotKey(
                None,  # hwnd = None -> el mensaje llega al hilo de la app
                HOTKEY_ID,
                MOD_CONTROL | MOD_SHIFT,
                VK_SPACE,
            )
        )
        self._registered = ok
        if ok:
            logger.info("Atajo global Ctrl+Shift+Espacio registrado.")
        else:
            logger.warning(
                "No se pudo registrar Ctrl+Shift+Espacio "
                "(posiblemente ya esta en uso por otra app)."
            )
        return ok

    def unregister(self) -> None:
        if self._registered:
            _user32.UnregisterHotKey(None, HOTKEY_ID)
            self._registered = False
            logger.info("Atajo global desregistrado.")

    # ------------------------------------------------------------------
    # Filtro de eventos nativos
    # ------------------------------------------------------------------

    def nativeEventFilter(self, eventType, message):
        """Captura WM_HOTKEY del hilo y dispara el callback."""
        if eventType == b"windows_generic_MSG":
            try:
                msg = ctypes.cast(int(message), ctypes.POINTER(Msg)).contents
            except (TypeError, ValueError):  # pragma: no cover
                return False, 0
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                logger.debug("WM_HOTKEY recibido.")
                self._on_triggered()
                return True, 0
        return False, 0