"""
core/launcher.py - Motor de apertura de aplicaciones.

Ejecuta la lista de apps asociadas a un modo de forma secuencial,
con un pequeno delay entre cada una para evitar picos de CPU.
"""

import os
import subprocess
import time
import logging
from typing import Callable

logger = logging.getLogger("jarvis.launcher")


class AppLauncher:
    """Lanza aplicaciones definidas en la configuracion de un modo."""

    # Delay (segundos) entre cada app para no saturar el disco
    LAUNCH_DELAY = 0.6

    def __init__(self) -> None:
        self._cancelled = False

    # ------------------------------------------------------------------
    # Cancelacion
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Detiene el lanzamiento pendiente."""
        self._cancelled = True

    def reset(self) -> None:
        """Resetea el flag de cancelacion."""
        self._cancelled = False

    # ------------------------------------------------------------------
    # Lanzamiento
    # ------------------------------------------------------------------

    def launch_mode(
        self,
        apps: list[dict[str, str]],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, str]:
        """
        Lanza todas las apps de un modo.

        Parameters
        ----------
        apps : lista de dicts con keys 'name', 'command' y opcionalmente 'args'.
        on_progress : callback(app_name, index, total) para notificar progreso.

        Returns
        -------
        dict con 'launched' y 'failed' como listas de nombres.
        """
        self._cancelled = False
        launched: list[str] = []
        failed: list[str] = []
        total = len(apps)

        for idx, app in enumerate(apps):
            if self._cancelled:
                logger.info("Lanzamiento cancelado por el usuario.")
                break

            name = app.get("name", "Desconocido")
            command = app.get("command", "")
            args = app.get("args", "")

            if on_progress:
                on_progress(name, idx + 1, total)

            success = self._open_app(command, args)
            if success:
                launched.append(name)
            else:
                failed.append(name)

            # Pausa entre apps (excepto la ultima)
            if idx < total - 1:
                time.sleep(self.LAUNCH_DELAY)

        self._cancelled = False
        return {"launched": launched, "failed": failed}

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _open_app(self, command: str, args: str = "") -> bool:
        """Abre una aplicacion individual. Retorna True si fue exitoso."""
        if not command:
            logger.warning("Comando vacio, saltando.")
            return False

        # Si es URL, abrir en navegador por defecto
        if command.startswith("http://") or command.startswith("https://"):
            try:
                os.startfile(command)
                logger.info(f"URL abierta: {command}")
                return True
            except OSError as exc:
                logger.error(f"Error abriendo URL {command}: {exc}")
                return False

        # Si el ejecutable no existe, intentar con os.startfile (registros Windows)
        if not os.path.exists(command):
            logger.warning(
                f"Ejecutable no encontrado: {command}. "
                "Intentando os.startfile..."
            )
            try:
                os.startfile(command)
                return True
            except OSError as exc:
                logger.error(f"No se pudo abrir {command}: {exc}")
                return False

        # Lanzamiento normal
        try:
            cmd_list = [command]
            if args:
                cmd_list.extend(args.split())
            subprocess.Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            logger.info(f"App lanzada: {command} {args}")
            return True
        except Exception as exc:
            logger.error(f"Error lanzando {command}: {exc}")
            # Fallback: os.startfile
            try:
                os.startfile(command)
                return True
            except OSError:
                return False
