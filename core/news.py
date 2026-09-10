"""
core/news.py - Servicio de noticias RSS/Atom del Jarvis Launcher.

Descarga y parsea fuentes RSS/Atom usando solo la stdlib de Python
(urllib + xml.etree), sin dependencias externas adicionales.

Noticias de ultima hora de varias fuentes de habla hispana
e internacionales, con soporte para feeds propios del usuario.
"""

from __future__ import annotations

import html
import logging
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger("jarvis.news")

# ----------------------------------------------------------------------
# Modelo
# ----------------------------------------------------------------------


@dataclass
class NewsItem:
    """Una noticia extraida de un feed."""

    title: str
    url: str
    source: str
    published: str = ""     # texto legible de la fecha
    guid: str = ""          # identificador unico del item (para dedup)
    extra: dict = field(default_factory=dict)


# ----------------------------------------------------------------------
# Fuentes predefinidas (RSS publicos estables)
# ----------------------------------------------------------------------

PRESET_SOURCES: list[dict[str, str]] = [
    {"name": "Google News (Mundo)", "url": "https://news.google.com/rss?hl=es&gl=CO&ceid=CO:es"},
    {"name": "BBC Mundo", "url": "https://feeds.bbci.co.uk/mundo/rss.xml"},
    {"name": "El Tiempo (Colombia)", "url": "https://www.eltiempo.com/rss/colombia.xml"},
    {"name": "El Espectador", "url": "https://www.elespectador.com/rss/"},
    {"name": "CNN en Español", "url": "https://cnnespanol.cnn.com/rss/"},
    {"name": "DW Noticias (Español)", "url": "https://rss.dw.com/rdf/rss-sp-all"},
    {"name": "RT en Español", "url": "https://actualidad.rt.com/feeds/all_es.rss"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
]

# Cabeceras de red (evitar bloqueos simples de algunos feeds)
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

_TIMEOUT = 8
_MAX_ITEMS_PER_SOURCE = 6
_REQUIRED_CHARS = 160


# ----------------------------------------------------------------------
# Parser RSS / Atom
# ----------------------------------------------------------------------


def _clean(text: str | None) -> str:
    """Limpia entidades HTML y espaciado excesivo."""
    if not text:
        return ""
    return html.unescape(" ".join(text.split()))


def _parse_date(value: str | datetime | None) -> datetime:
    """Convierte fechas RSS (RFC822/ISO) a datetime aware (UTC)."""
    if value is None:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        dt = None
        for fmt in (
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S",
            "%d %b %Y %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            dt = datetime(1970, 1, 1, tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_feed(xml_text: str, source: str) -> list[NewsItem]:
    """Parsea un documento XML y devuelve items de noticias."""
    root = ET.fromstring(xml_text)
    items: list[NewsItem] = []

    # Detectar tipo de feed por el tag raiz
    tag = root.tag.lower().split("}")[-1]
    channel = None
    if tag == "feed":            # Atom
        channel = root
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for entry in entries[: _MAX_ITEMS_PER_SOURCE]:
            title = _clean(entry.findtext("{http://www.w3.org/2005/Atom}title"))
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            url = link_el.get("href") if link_el is not None else ""
            pub = _clean(entry.findtext("{http://www.w3.org/2005/Atom}updated"))
            guid = _clean(entry.findtext("{http://www.w3.org/2005/Atom}id")) or url
            if not (title and url):
                continue
            items.append(_make_item(title, url, source, pub, guid, entry))
    else:                        # RSS 2.0
        channel = root.find("channel")
        if channel is None:
            return items
        entries = channel.findall("item")
        ns = {"media": "http://search.yahoo.com/mrss/"}
        for entry in entries[: _MAX_ITEMS_PER_SOURCE]:
            title = _clean(entry.findtext("title"))
            url = _clean(entry.findtext("link"))
            pub = _clean(entry.findtext("pubDate"))
            guid = _clean(entry.findtext("guid")) or url
            if not (title and url):
                continue
            items.append(_make_item(title, url, source, pub, guid, entry, ns))

    items.sort(key=lambda it: _parse_date(it.extra.get("_dt")), reverse=True)
    return items


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _make_item(
    title: str,
    url: str,
    source: str,
    pub: str,
    guid: str,
    entry: ET.Element,
    ns: dict | None = None,
) -> NewsItem:
    """Construye un NewsItem con datos extra (fecha, imagen, resumen)."""
    ns = ns or {}
    # Fecha máquina
    dt = _parse_date(pub)
    extra: dict = {"_dt": dt}

    # Descripcion/resumen
    desc = _clean(entry.findtext("description", default="")) if ns else ""
    if not desc:
        nested = entry.find("summary")
        if nested is not None:
            desc = _clean(nested.text)
    extra["summary"] = desc[:_REQUIRED_CHARS]

    # Imagen si el feed la provee (media:content / enclosure)
    image = ""
    if ns:
        media = entry.find("media:content", ns)
        if media is None:
            media = entry.find("media:thumbnail", ns)
        if media is not None:
            image = media.get("url", "")
    if not image:
        enc = entry.find("enclosure")
        if enc is not None and enc.get("type", "").startswith("image"):
            image = enc.get("url", "")
    extra["image"] = image

    # Fecha legible
    if dt.year > 1970:
        human = dt.strftime("%d %b %H:%M")
    else:
        human = pub or ""
    extra["_human"] = human

    return NewsItem(
        title=title,
        url=url,
        source=_clean(source),
        published=human,
        guid=guid,
        extra=extra,
    )


def _iso_ts() -> str:
    """Timestamp ISO local para log y depuracion."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


# ----------------------------------------------------------------------
# Cliente HTTP minimalista (sin requests)
# ----------------------------------------------------------------------


def _fetch_feed(url: str, timeout: int = _TIMEOUT) -> str:
    """Descarga el contenido de una URL con cabeceras de navegador."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        raw = resp.read()
        return raw.decode("utf-8", errors="replace")


class NewsService:
    """
    Servicio de noticias con cache en memoria y fetch bajo demanda.

    - `fetch(source_urls)`: devuelve items combinados y ordenados por fecha.
    - Corre en un hilo aparte desde la UI (no bloquear el repintado).
    """

    def __init__(self, cache_size: int = 40) -> None:
        self._cache: dict[str, list[NewsItem]] = {}
        self._cache_size = cache_size

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def fetch_sources(self, sources: list[dict[str, str]]) -> list[NewsItem]:
        """
        Descarga y combina varias fuentes (["name", "url"]).

        Returns
        -------
        Items unicos por guid, ordenados de mas reciente a mas antiguo.
        """
        all_items: list[NewsItem] = []
        seen: set[str] = set()

        for source in sources:
            name = source.get("name", "Noticias")
            url = source.get("url", "")
            if not url:
                continue
            try:
                items = self._fetch_single(url, name)
            except Exception as exc:  # noqa: BLE001 - red no confiable
                logger.warning("Feed [%s] fallo: %s", name, exc)
                items = []

            for item in items:
                key = item.guid or item.url
                if key in seen:
                    continue
                seen.add(key)
                all_items.append(item)

        # Ordenar por fecha desc
        all_items.sort(
            key=lambda it: _parse_date(it.extra.get("_dt")),
            reverse=True,
        )
        return all_items

    def _fetch_single(self, url: str, name: str) -> list[NewsItem]:
        """Fetch de una sola fuente con cache por timestamp."""
        now = time.time()
        cached = self._cache.get(url)
        if cached:
            # Refrescar si el cache tiene mas de 600 segundos
            cached_dt = _parse_date(cached[0].extra.get("_dt"))
            try:
                age = now - cached_dt.timestamp()
            except (OverflowError, OSError):
                age = 9999
            if cached_dt.year > 1970 and age < 600:
                return cached

        xml_text = _fetch_feed(url)
        items = _parse_feed(xml_text, name)

        # Cache ligero
        self._cache[url] = items[: self._cache_size]
        if len(self._cache) > 30:      # evaporar caches viejos
            self._cache.clear()
        return items

    def validate_url(self, url: str) -> bool:
        """Verifica que una URL sea un feed RSS/Atom usable."""
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return False
        try:
            xml_text = _fetch_feed(url)
            _parse_feed(xml_text, "test")
            return True
        except Exception:  # noqa: BLE001
            return False

    # Backward-compat alias
    fetch = fetch_sources