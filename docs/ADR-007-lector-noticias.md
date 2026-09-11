# ADR-007: Lector de noticias a pantalla completa (spec v2 puntos 3 y 4)

- **Estado**: Aceptado
- **Fecha**: 2026-09-11 (America/Bogota)
- **Versión asociada**: v2.0.0 (rama `feat/news-reader`)
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode),
  Kuro-chan (frontend)
- **Tipo**: Feature / interacción nueva

## Contexto

El diseño v2 (modo foco/workspace) pide en los puntos 3 y 4 un **lector de
noticias a pantalla completa** para leer sin salir del launcher:

1. Al hacer clic en una noticia del panel no basta con abrir el navegador: se
   quiere una **vista de lectura** dentro del launcher.
2. Debe permitir **navegar la lista sin volver atrás** (cambiar de artículo
   directamente).
3. Tipografía y jerarquía adecuadas para **lectura larga** (lead, cita
   destacada, cuerpo cómodo), coherente con la estética HUD y los temas.
4. **Sin dependencias nuevas** y respetando el ADR-001 (sin `QGraphicsEffect`).

Restricción técnica heredada: el parser RSS/Atom (`core/news.py`) entrega
`NewsItem` con `title`, `url`, `published`, `source` y `extra["summary"]`
(fragmento limpio de ~160+ caracteres). **Los feeds no traen el cuerpo completo
del artículo** en general; el cuerpo real vive en la URL del artículo.

## Opciones consideradas

| Opción | Implementación | Ventajas | Desventajas | Veredicto |
|--------|---------------|----------|-------------|-----------|
| A1. Widget interno fullscreen (hijo de JarvisUI) | `NewsReaderView(QWidget)` sobre el launcher (mismo patrón que BootOverlay) | Coherente con el HUD; un solo top-level; fade con windowOpacity | Lector siempre presente en la clase principal | ✅ Elegida |
| A2. Ventana separada (QDialog/QWindow) | Nuevo top-level | Aislado y testeable por separado | Rompe la inmersión; z-order a gestionar | Alternativa |
| A3. Browser embebido (QWebEngineView) | Widget Chromium | Render HTML real | Dependencia nueva pesada; fuera de restricción | ❌ No |
| B1. Abrir siempre en navegador | Flujo v1 | Simple | No es un lector | ❌ No cumple spec |
| B2. Fetch de la URL + extracción de texto (parser propio) | `urllib` + HTMLParser | Cuerpo completo offline | Parser sin libs es frágil y costoso; **no garantiza** resultado en feeds variados | ⚠️ Descartado por costo |
| B3. Contenido del feed + botón "Abrir original" | usar `extra["summary"]` como lead/cuerpo; `webbrowser.open` al original | Cero deps; resultado predecible; el original queda a un clic | No trae el cuerpo completo offline | ✅ Elegida |
| C1. Split-pane redimensionable | `QSplitter` (lista izquierda + lectura derecha) | Navegas y lees sin volver atrás | Más código de layout | ✅ Elegida |
| C2. Vista única con back | Un solo panel | Más simple | Cada artículo obliga a volver | Descartada |

## Decision

1. **`ui/news_reader.py` — `NewsReaderView(QWidget)`**, hijo a pantalla
   completa de `JarvisUI` (mismo patrón de overlay que `BootOverlay`, con
   `setGeometry(parent.rect())` y `raise_()`):
   - **Split-pane** con `QSplitter` horizontal: lista compacta izquierda
     (180–380 px, `MiniNewsItem` con título + fuente/hora; selección resaltada)
     y lectura derecha con `QTextBrowser`.
   - **Contenido desde el feed** (decisión B3): `extra["summary"]` dividido por
     `_split_readable()` en **lead** (2 primeras oraciones), **pull-quote**
     (primera oración) y **cuerpo** (resto). Si no hay resumen, mensaje neutro
     y el protagonismo lo toma **"Abrir original ↗"**.
   - **Tipografía de lectura larga**: columna centrada `max-width:760px`,
     título Georgia 26 px, meta fuente·hora en dim, **capitular** (primera
     letra del lead en acento), **pull-quote** en cursiva con barra lateral de
     acento y divisores tipográficos (`<hr>` del tema). Todo el HTML se genera
     con los colores del `ThemeManager` activo (temas vivos al cambiar).
   - **Navegación**: `←`/`→` cambian de artículo, `Escape` vuelve al launcher
     (señal `closeRequested`); el panel también navega con clic; al cambiar de
     artículo el scroll vuelve arriba.
   - Sin `QGraphicsEffect`: fade de entrada con `windowOpacity` (ADR-001).
2. **Integración en `ui/news_panel.py`**: el clic deja de llamar
   `webbrowser.open` y emite `readerRequested(list[NewsItem], int)` (el índice
   del artículo pulsado). El enlace original vive en el botón del lector.
3. **Integración en `ui/jarvis_ui.py`**: `_open_reader(items, index)` crea el
   lector bajo demanda, lo muestra con fade y aplica el tema; `_close_reader()`
   oculta el lector y devuelve el foco al launcher; `keyPressEvent` prioriza los
   atajos del lector cuando está visible.

## Consecuencias

- **Positivas**: la lectura ocurre dentro del launcher en estética HUD con los
  temas; la lista y el artículo están siempre visibles; cero dependencias
  nuevas; el flujo v1 (navegador) no se pierde — queda a un clic en el lector.
- **Límites**: el cuerpo visualizado es el fragmento del feed (no el artículo
  completo offline); no se implementa extracción desde la URL del artículo
  (descartada por fragilidad sin librerías). Si en el futuro se quiere cuerpo
  completo, el ADR registra la vía: agregar un extractor de contenido con la
  dependencia apropiada, fuera de costo de esta fase.
- **Pruebas**: render del splitter, mini-items, navegación `←/→`, división
  lead/pull-quote/body, HTML con capitular/cita, temas, respaldo sin summary e
  integración (clic → lector → Escape) pasan en offscreen. La validación
  visual final se hará en la máquina real.

## Referencias

- [ADR-001](./ADR-001-quitar-qgraphicseffect.md)
- [ADR-005](./ADR-005-panel-noticias-rss.md) (origen de `NewsItem` y del panel)
- [ADR-006](./ADR-006-atajo-global-bandeja.md) (mismo ciclo de vida de overlay)
- Sección 3 de [Arquitectura.md](./Arquitectura.md): `ui/news_reader.py`,
  `ui/news_panel.py`, `ui/jarvis_ui.py`