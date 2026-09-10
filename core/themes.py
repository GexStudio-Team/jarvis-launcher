"""
core/themes.py - Temas de color del Jarvis Launcher.

Cada tema define una paleta completa (fondo, texto, acento, vidrio de las
cards y colores HUD). Los widgets leen los colores via ThemeManager para
pintar sus propios paintEvent sin QSS global fragil.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Paleta de colores de un tema."""

    id: str
    name: str
    bg: str                # color de fondo principal
    bg_alt: str            # tono alterno para gradientes/paneles
    text: str              # texto principal
    text_dim: str          # texto secundario / apagado
    accent: str            # color de acento (cyan por defecto)
    accent_soft: str       # tono suave del acento (para fondos)
    card_bg: str           # fondo de las tarjetas (glass)
    card_border: str       # borde base de las tarjetas
    grid: str              # color de la grilla de fondo
    scan: str              # linea de escaneo
    ring_outer: str        # anillo HUD exterior
    ring_mid: str          # anillo HUD medio
    ring_inner: str        # anillo HUD interior
    particle: str          # color de particulas
    is_dark: bool          # si es tema oscuro (para texto inverso)


# ----------------------------------------------------------------------
# Paletas disponibles
# ----------------------------------------------------------------------

THEMES: dict[str, Theme] = {
    "obsidiana": Theme(
        id="obsidiana",
        name="Obsidiana (clásico)",
        bg="#080A12",
        bg_alt="#0E1420",
        text="#FFFFFF",
        text_dim="#8A93A6",
        accent="#00FFFF",
        accent_soft="#002F3F",
        card_bg="#141A26",
        card_border="#2A3546",
        grid="#00FFFF",
        scan="#00FFFF",
        ring_outer="#0064B4",
        ring_mid="#00B4DC",
        ring_inner="#00FFFF",
        particle="#00FFFF",
        is_dark=True,
    ),
    "nocturno": Theme(
        id="nocturno",
        name="Nocturno (azul profundo)",
        bg="#05070F",
        bg_alt="#0B1226",
        text="#E8EEFF",
        text_dim="#7C8CB8",
        accent="#4D8DFF",
        accent_soft="#0F1E45",
        card_bg="#101A33",
        card_border="#24345C",
        grid="#4D8DFF",
        scan="#4D8DFF",
        ring_outer="#1B3A8C",
        ring_mid="#2F66D9",
        ring_inner="#4D8DFF",
        particle="#4D8DFF",
        is_dark=True,
    ),
    "crimson": Theme(
        id="crimson",
        name="Crimson (gótico)",
        bg="#12060A",
        bg_alt="#210D14",
        text="#F5E6EA",
        text_dim="#B08A93",
        accent="#FF2D55",
        accent_soft="#3C0D1A",
        card_bg="#22101A",
        card_border="#4A1B26",
        grid="#FF2D55",
        scan="#FF2D55",
        ring_outer="#8C1B36",
        ring_mid="#E02446",
        ring_inner="#FF2D55",
        particle="#FF2D55",
        is_dark=True,
    ),
    "esmeralda": Theme(
        id="esmeralda",
        name="Esmeralda (verde neón)",
        bg="#06100A",
        bg_alt="#0A1C12",
        text="#E6F5EC",
        text_dim="#8AB39C",
        accent="#30D158",
        accent_soft="#0B3319",
        card_bg="#0F2418",
        card_border="#1F4830",
        grid="#30D158",
        scan="#30D158",
        ring_outer="#1B8C3E",
        ring_mid="#26B850",
        ring_inner="#30D158",
        particle="#30D158",
        is_dark=True,
    ),
    "matriz": Theme(
        id="matriz",
        name="Matriz (verde terminal)",
        bg="#020803",
        bg_alt="#05120A",
        text="#C8FFD8",
        text_dim="#5F9E74",
        accent="#00FF66",
        accent_soft="#0A3B1E",
        card_bg="#07130C",
        card_border="#123823",
        grid="#00FF66",
        scan="#00FF66",
        ring_outer="#008C40",
        ring_mid="#00CC58",
        ring_inner="#00FF66",
        particle="#00FF66",
        is_dark=True,
    ),
    "violeta": Theme(
        id="violeta",
        name="Violeta (neón púrpura)",
        bg="#0D0618",
        bg_alt="#180B2E",
        text="#F0E6FF",
        text_dim="#A08AB8",
        accent="#BF5AFF",
        accent_soft="#2E1250",
        card_bg="#1B1033",
        card_border="#3A1F63",
        grid="#BF5AFF",
        scan="#BF5AFF",
        ring_outer="#6A1BB8",
        ring_mid="#9A3CE0",
        ring_inner="#BF5AFF",
        particle="#BF5AFF",
        is_dark=True,
    ),
    "ambar": Theme(
        id="ambar",
        name="Ámbar (retro terminal)",
        bg="#0F0A02",
        bg_alt="#1E1505",
        text="#FFE9B8",
        text_dim="#B39155",
        accent="#FFB020",
        accent_soft="#3C2504",
        card_bg="#1E1505",
        card_border="#4A3412",
        grid="#FFB020",
        scan="#FFB020",
        ring_outer="#B87700",
        ring_mid="#E09B10",
        ring_inner="#FFB020",
        particle="#FFB020",
        is_dark=True,
    ),
    "luz": Theme(
        id="luz",
        name="Luz (claro limpio)",
        bg="#F2F5FA",
        bg_alt="#FFFFFF",
        text="#16202E",
        text_dim="#5C6B84",
        accent="#0066FF",
        accent_soft="#D6E6FF",
        card_bg="#FFFFFF",
        card_border="#C8D2E4",
        grid="#0066FF",
        scan="#0066FF",
        ring_outer="#7FA8E8",
        ring_mid="#4D8DFF",
        ring_inner="#0066FF",
        particle="#0066FF",
        is_dark=False,
    ),
    "nieve": Theme(
        id="nieve",
        name="Nieve (claro minimal)",
        bg="#FAFAFC",
        bg_alt="#FFFFFF",
        text="#1C2333",
        text_dim="#6A7A96",
        accent="#38B6FF",
        accent_soft="#DDEEFF",
        card_bg="#FFFFFF",
        card_border="#D4DCE8",
        grid="#38B6FF",
        scan="#38B6FF",
        ring_outer="#7FC9F0",
        ring_mid="#55B9F0",
        ring_inner="#38B6FF",
        particle="#38B6FF",
        is_dark=False,
    ),
}


class ThemeManager:
    """Resuelve el tema activo y expone los colores por rol."""

    def __init__(self, theme_id: str = "obsidiana") -> None:
        self._theme_id = theme_id if theme_id in THEMES else "obsidiana"

    # ------------------------------------------------------------------
    # Acceso al tema
    # ------------------------------------------------------------------

    @property
    def theme_id(self) -> str:
        return self._theme_id

    @theme_id.setter
    def theme_id(self, value: str) -> None:
        if value in THEMES:
            self._theme_id = value

    @property
    def theme(self) -> Theme:
        return THEMES[self._theme_id]

    def set_theme(self, theme_id: str) -> None:
        """Cambia el tema activo (ignora ids invalidos)."""
        if theme_id in THEMES:
            self._theme_id = theme_id

    @staticmethod
    def available_themes() -> list[Theme]:
        """Devuelve todos los temas disponibles (orden estable)."""
        return list(THEMES.values())

    def color(self, role: str) -> str:
        """Devuelve el color de un rol del tema activo."""
        return getattr(self.theme, role, self.theme.accent)

    # ------------------------------------------------------------------
    # Helpers de conversion
    # ------------------------------------------------------------------

    @staticmethod
    def to_qcolor(hex_color: str) -> "QColor":  # noqa: F821
        """Convierte un color hex a QColor (import perezoso para no acoplar UI)."""
        from PyQt6.QtGui import QColor
        return QColor(hex_color)

    @staticmethod
    def rgba(hex_color: str, alpha: int) -> "QColor":  # noqa: F821
        """QColor con alpha aplicado (0-255)."""
        q = ThemeManager.to_qcolor(hex_color)
        q.setAlpha(int(alpha))
        return q