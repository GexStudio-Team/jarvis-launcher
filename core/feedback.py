"""
core/feedback.py - Retroalimentacion sonora del launcher.

Usa winsound.Beep (tonos generados por el altavoz interno de Windows)
con fallback silencioso en otras plataformas. Los tonos se reproducen
en hilos daemon para no bloquear el hilo de la UI.

NOTA: se evita PlaySound(SND_ALIAS) porque depende del "esquema de
sonidos de Windows" (si la PC tiene sonidos de sistema desactivados,
no se escucha nada). Beep con frecuencias funciona en todos los casos.
"""

import sys
import threading

_HAS_WINSOUND = False
try:
    import winsound

    _HAS_WINSOUND = True
except ImportError:  # pragma: no cover - solo en no-Windows
    pass


def _beep(freq: int, ms: int) -> None:
    """Reproduce un tono en un hilo separado (no bloqueante)."""
    if not _HAS_WINSOUND:
        return
    threading.Thread(
        target=lambda: winsound.Beep(freq, ms),
        daemon=True,
    ).start()


def play_click() -> None:
    """Sonido breve y brillante al seleccionar un modo (click directo)."""
    _beep(1250, 60)


def play_success() -> None:
    """Arpegio ascendente (mi5 -> la5) al completar sin errores."""
    _beep(987, 90)
    _beep(1319, 140)


def play_error() -> None:
    """Tono grave y corto cuando hubo apps que fallaron."""
    _beep(220, 260)


def play_cancel() -> None:
    """Tono descendente al cancelar una operacion."""
    _beep(420, 90)
    _beep(280, 140)