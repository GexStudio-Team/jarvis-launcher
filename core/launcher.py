"""
core/launcher.py - Motor de apertura de aplicaciones.

Ejecuta la lista de apps asociadas a un modo de forma secuencial,
con un pequeno delay entre cada una para evitar picos de CPU.

Resolucion de comandos (en orden):
  1. Si el comando es una URL -> navegador por defecto.
  2. Si la ruta existe -> se lanza directamente.
  3. Si el comando es un nombre corto (p. ej. "Discord") o la ruta
     no existe -> se busca el ejecutable en el menu de inicio del
     usuario y del sistema (accesos directos .lnk) y en el registro
     App Paths de Windows.
  4. Si no se encuentra -> fallo con mensaje descriptivo.
"""

import glob
import logging
import os
import shutil
import subprocess
import time
import winreg
from typing import Callable

logger = logging.getLogger("jarvis.launcher")

# Directorios del menu de inicio donde buscar accesos directos
_START_MENU_DIRS = [
    os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
    os.path.join(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
        r"Microsoft\Windows\Start Menu\Programs",
    ),
]


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

        # Resolver la ruta real del ejecutable
        resolved = self._resolve_command(command)
        if resolved is None:
            logger.error(
                f"No se encontro la aplicacion '{command}'. "
                "Verifica que este instalada o corrige la ruta en config.json."
            )
            return False

        # Lanzamiento normal
        try:
            cmd_list = [resolved]
            if args:
                cmd_list.extend(args.split())
            subprocess.Popen(
                cmd_list,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            logger.info(f"App lanzada: {resolved} {args}")
            return True
        except Exception as exc:
            logger.error(f"Error lanzando {resolved}: {exc}")
            # Fallback: os.startfile
            try:
                os.startfile(resolved)
                return True
            except OSError:
                return False

    # ------------------------------------------------------------------
    # Resolucion de comandos
    # ------------------------------------------------------------------

    def _resolve_command(self, command: str) -> str | None:
        """Devuelve la ruta real del ejecutable o None si no existe."""
        # 1. Ruta absoluta existente
        if os.path.exists(command):
            return command

        # 2. Ejecutable en el PATH
        found = shutil.which(command)
        if found:
            return found

        # 3. Nombre en menu de inicio (usuario y sistema)
        exe_name = os.path.basename(command).split(".exe")[0]
        found = self._find_in_start_menu(exe_name)
        if found:
            return found

        # 4. Registro App Paths de Windows (HKCU y HKLM)
        found = self._find_in_app_paths(command)
        if found:
            return found

        return None

    def _find_in_start_menu(self, app_name: str) -> str | None:
        """
        Busca un acceso directo .lnk cuyo nombre coincida con app_name
        (insensible a mayusculas) y extrae el TargetPath del ejecutable.
        """
        app_lower = app_name.lower()
        for start_dir in _START_MENU_DIRS:
            if not os.path.isdir(start_dir):
                continue
            pattern = os.path.join(start_dir, "**", "*.lnk")
            for lnk in glob.glob(pattern, recursive=True):
                base = os.path.splitext(os.path.basename(lnk))[0].lower()
                if app_lower in base:
                    target = self._read_lnk_target(lnk)
                    if target and os.path.exists(target) and target.lower().endswith(".exe"):
                        logger.info(f"App '{app_name}' resuelta via: {lnk}")
                        return target
        return None

    @staticmethod
    def _read_lnk_target(lnk_path: str) -> str | None:
        """Extrae TargetPath de un .lnk usando WScript.Shell (COM via PowerShell)."""
        import subprocess as sp

        ps_script = (
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
            f"'{lnk_path}'); $s.TargetPath"
        )
        try:
            out = sp.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=sp.CREATE_NO_WINDOW,
            )
            target = out.stdout.strip()
            return target if target else None
        except Exception as exc:  # pragma: no cover
            logger.warning(f"No se pudo leer el acceso directo {lnk_path}: {exc}")
            return None

    def _find_in_app_paths(self, command: str) -> str | None:
        """Busca el ejecutable en la clave App Paths del registro."""
        exe_name = os.path.basename(command)
        if not exe_name.lower().endswith(".exe"):
            exe_name += ".exe"

        base_key = r"Software\Microsoft\Windows\CurrentVersion\App Paths"
        candidates = [
            (winreg.HKEY_CURRENT_USER, rf"{base_key}\{exe_name}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"{base_key}\{exe_name}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"Software\WOW6432Node\{base_key}\{exe_name}"),
        ]

        for hive, key_path in candidates:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    value, _ = winreg.QueryValueEx(key, "")
                    if value and os.path.exists(value):
                        logger.info(f"App '{command}' resuelta via App Paths: {value}")
                        return value
            except OSError:
                continue
        return None