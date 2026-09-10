"""
main.py - Entry point del J.A.R.V.I.S. Launcher.

Carga la configuracion, construye la interfaz y coordina el lanzamiento
de aplicaciones cuando el usuario selecciona un modo.
"""

import sys
import os
import socket
import logging
import threading

from PyQt6.QtWidgets import QApplication

# Asegurar que los modulos del proyecto estan en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ConfigManager
from core.launcher import AppLauncher
from ui.jarvis_ui import JarvisUI

# -----------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("jarvis.main")

# -----------------------------------------------------------------------
# Singleton check - evitar dos instancias simultaneas
# -----------------------------------------------------------------------
SOCKET_PORT = 47821


def _is_already_running() -> bool:
    """Intenta bindear un puerto para detectar otra instancia."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sock.bind(("127.0.0.1", SOCKET_PORT))
        sock.listen(1)
        return False
    except OSError:
        return True


# -----------------------------------------------------------------------
# Callback de seleccion de modo
# -----------------------------------------------------------------------

def _handle_mode_selected(launcher: AppLauncher, ui: JarvisUI, config: ConfigManager):
    """Retorna un closure que maneja la seleccion de modo."""

    def handler(mode_id: str) -> None:
        mode = config.get_mode(mode_id)
        if mode is None:
            ui.set_launch_complete("Error", [], ["Modo no encontrado"])
            return

        apps = mode.get("apps", [])
        if not apps:
            ui.set_launch_complete(
                mode.get("name", mode_id), [], ["No hay apps configuradas"]
            )
            return

        mode_name = mode.get("name", mode_id)
        logger.info(f"Modo seleccionado: {mode_name} ({len(apps)} apps)")

        # Lanzar en un hilo separado para no bloquear la UI
        def _run_launch():
            result = launcher.launch_mode(apps)
            # Actualizar UI en el hilo principal
            ui.set_launch_complete(
                mode_name, result["launched"], result["failed"]
            )
            logger.info(
                f"Resultado: {len(result['launched'])} OK, "
                f"{len(result['failed'])} fallos"
            )

        thread = threading.Thread(target=_run_launch, daemon=True)
        thread.start()

    return handler


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> int:
    # Verificar instancia unica
    if _is_already_running():
        logger.warning("Ya hay una instancia ejecutandose. Cerrando.")
        return 0

    # Cargar configuracion
    config = ConfigManager()
    logger.info(f"Configuracion cargada: {config.app_name}")

    # Crear app Qt
    app = QApplication(sys.argv)
    app.setApplicationName("J.A.R.V.I.S. Launcher")
    app.setApplicationVersion(config._config.get("version", "1.0.0"))

    # Estilo global
    app.setStyleSheet(
        """
        * {
            font-family: 'Segoe UI', 'Consolas', monospace;
        }
        QWidget {
            background: #080A12;
            color: white;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 6px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 255, 255, 40);
            border-radius: 3px;
            min-height: 30px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
    )

    # Crear launcher
    launcher = AppLauncher()

    # Crear ventana principal
    handler = _handle_mode_selected(launcher, ui=None, config=config)
    ui = JarvisUI(config._config, on_mode_selected=handler)
    handler_ui = _handle_mode_selected(launcher, ui, config)
    ui._on_mode_selected = handler_ui

    ui.show()

    logger.info("J.A.R.V.I.S. Launcher iniciado.")
    exit_code = app.exec()

    logger.info("Cerrando J.A.R.V.I.S. Launcher.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
