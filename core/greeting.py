"""
core/greeting.py - Saludo dinámico del launcher (hora + adjetivo rotativo).

Genera el mensaje de bienvenida del launcher segun:
  1. Franja horaria: Buenos dias (05:00-12:00), Buenas tardes
     (12:00-19:00), Buenas noches (19:00-05:00).
  2. Adjetivo rotativo por arranque (Desarrollador, Ingeniero, Arquitecto,
     Creador, Hacker, Explorador, Maestro, Visionario, Estratega, Artesano).
  3. Nombre real si la cuenta de GitHub esta vinculada; en caso contrario
     usa el adjetivo ("Buenos dias, Ingeniero" / "Buenos dias, Duvan").
"""

from __future__ import annotations

from datetime import datetime

ADJECTIVES = [
    "Desarrollador",
    "Ingeniero",
    "Arquitecto",
    "Creador",
    "Hacker",
    "Explorador",
    "Maestro",
    "Visionario",
    "Estratega",
    "Artesano",
]


def greeting_for(now: datetime, display_name: str) -> str:
    """Devuelve el saludo completo para la hora y nombre dados.

    Parameters
    ----------
    now : hora actual del sistema.
    display_name : nombre a mostrar (adjetivo rotativo o nombre real de
        GitHub cuando la cuenta esta vinculada). Nunca vacio.
    """
    hour = now.hour
    if 5 <= hour < 12:
        part = "Buenos dias"
    elif 12 <= hour < 19:
        part = "Buenas tardes"
    else:
        part = "Buenas noches"
    return f"{part}, {display_name}."