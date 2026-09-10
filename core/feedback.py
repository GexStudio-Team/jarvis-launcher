"""
core/feedback.py - Retroalimentacion sonora del launcher.

Usa winsound (Windows) con fallback silencioso en otras plataformas.
"""

import sys

_HAS_WINSOUND = False
try:
    import winsound

    _HAS_WINSOUND = True
except ImportError:  # pragma: no cover - solo en no-Windows
    pass


def play_click() -> None:
    """Sonido breve al seleccionar un modo."""
    if _HAS_WINSOUND:
        winsound.PlaySound(
            "SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC
        )


def play_success() -> None:
    """Sonido al completar el lanzamiento sin errores."""
    if _HAS_WINSOUND:
        winsound.PlaySound(
            "SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC
        )


def play_error() -> None:
    """Sonido cuando hubo apps que fallaron al lanzar."""
    if _HAS_WINSOUND:
        winsound.PlaySound(
            "SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC
        )


def play_cancel() -> None:
    """Sonido al cancelar una operacion."""
    if _HAS_WINSOUND:
        winsound.Beep(220, 150)