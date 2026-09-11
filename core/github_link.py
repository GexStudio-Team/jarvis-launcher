"""
core/github_link.py - Vinculacion con la cuenta de GitHub del usuario.

Permite que el launcher salude al usuario por su nombre REAL (el que aparece
en su perfil publico de GitHub), no un adjetivo generico.

Flujo de vinculacion:
  1. Deteccion automatica: si existe el CLI `gh` autenticado, se consulta
     `gh api user` y se extrae login + nombre real sin guardar secretos.
  2. Verificacion manual: si `gh` no esta disponible o no esta autenticado,
     el usuario escribe su username y se valida contra la API publica
     GET https://api.github.com/users/{username} (mismo patron urllib que
     usa NewsService en core/news.py).

Sin dependencias nuevas (urllib de la stdlib) y sin exponer tokens: solo se
persiste el username y el nombre publico en settings.json.
"""

from __future__ import annotations

import json
import logging
import subprocess
import urllib.error
import urllib.request

logger = logging.getLogger("jarvis.github")


def detect_gh_identity() -> tuple[str, str] | None:
    """Detecta login + nombre real con el CLI `gh` autenticado (sin secretos).

    Returns
    -------
    (login, name) si se pudo detectar; None en caso contrario.
    name puede ser vacio si el perfil no define un nombre publico.
    """
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode != 0:
            logger.debug("gh no autenticado o no disponible: %s", result.stderr.strip())
            return None
        login = result.stdout.strip()
        if not login:
            return None
        name_result = subprocess.run(
            ["gh", "api", "user", "--jq", ".name // empty"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        name = name_result.stdout.strip() if name_result.returncode == 0 else ""
        logger.info("Identidad GitHub detectada: login=%r name=%r", login, name)
        return login, name
    except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
        logger.debug("Fallo la deteccion con gh: %s", exc)
        return None


def verify_username(username: str) -> tuple[str, str] | None:
    """Verifica un username contra la API publica de GitHub.

    Returns
    -------
    (username_normalizado, name) si el perfil existe; None si no.
    """
    username = username.strip().lstrip("@")
    if not username:
        return None
    url = f"https://api.github.com/users/{username}"
    request = urllib.request.Request(url, headers={"User-Agent": "jarvis-launcher"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.HTTPError) as exc:  # noqa: F821
        if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
            logger.info("Username %r no existe en GitHub.", username)
        else:
            logger.debug("Error consultando la API de GitHub: %s", exc)
        return None
    name = (data.get("name") or "").strip()
    login = (data.get("login") or username).strip()
    logger.info("Username verificado: login=%r name=%r", login, name)
    return login, name