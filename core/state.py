"""
core/state.py - Gestor de estado de la aplicacion (state.json).

Registra el historial de modos usados y el ultimo modo seleccionado.
Persistencia local en la raiz del proyecto.
"""

import json
import os
from datetime import datetime
from typing import Any


class StateManager:
    """Persiste y lee el estado local del launcher."""

    MAX_HISTORY = 5

    def __init__(self, state_path: str | None = None) -> None:
        if state_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            state_path = os.path.join(base_dir, "state.json")
        self.state_path = state_path
        self._state: dict[str, Any] = self._load()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save(self) -> None:
        try:
            with open(self.state_path, "w", encoding="utf-8") as fh:
                json.dump(self._state, fh, indent=4, ensure_ascii=False)
        except OSError as exc:
            print(f"[state] No se pudo guardar state.json: {exc}")

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def record_mode(self, mode_id: str, mode_name: str) -> None:
        """Registra un modo utilizado y persiste el estado."""
        entry = {
            "id": mode_id,
            "name": mode_name,
            "at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        self._state["last_mode"] = entry
        history = self._state.setdefault("history", [])
        # Evitar duplicados consecutivos
        if history and history[0].get("id") == mode_id:
            history[0] = entry
        else:
            history.insert(0, entry)
        self._state["history"] = history[: self.MAX_HISTORY]
        self.save()

    def get_last_mode(self) -> dict[str, str] | None:
        """Devuelve el ultimo modo usado o None."""
        return self._state.get("last_mode")

    def get_history(self) -> list[dict[str, str]]:
        """Devuelve el historial de modos recientes."""
        return self._state.get("history", [])