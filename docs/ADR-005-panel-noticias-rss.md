# ADR-005: Panel lateral de noticias RSS (sin dependencias nuevas)

- **Estado**: Aceptado
- **Fecha**: 2026-09-10 (America/Bogota)
- **Versión asociada**: v1.4.0
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode)
- **Tipo**: Feature / integración externa

## Contexto

v1.4 pide un panel lateral de noticias en el launcher: conectable a una fuente
(navegando entre presets RSS o pegando una URL propia), con posición
izquierda/derecha, ancho redimensionable por el borde y apertura de la noticia
en el navegador al hacer clic. El panel debe actualizarse solo (timer) y
definir un estado "desconectado" claro con botón para conectar.

Restricciones heredadas: no agregar dependencias nuevas (el proyecto corre
con Python estándar + PyQt6) y respetar ADR-001 (sin `QGraphicsEffect`; todo
efecto pintado a mano).

## Decision

1. **Nuevo módulo `core/news.py`** usando **solo la biblioteca estándar**:
   - `NewsService`: descarga con `urllib.request` y parsea con
     `xml.etree.ElementTree` feeds **RSS 2.0 y Atom** (detección por tag).
   - `NewsItem`: modelo con `title`, `link`, `source`, `published`
     (datetime **aware UTC** normalizado) y helper `time_ago()`.
   - `PRESET_SOURCES`: 10 fuentes predefinidas (Google News Mundo, BBC
     Mundo, El Tiempo, El Espectador, CNN en Español, DW, RT, Hacker News,
     The Verge, Wired).
   - Parseo de fechas tolerante (varios formatos + datetime directo) con
     normalización a UTC aware (evita comparaciones naive/aware).
2. **`ui/news_panel.py`** — `NewsPanel` (QFrame):
   - Posición y ancho (280–560 px) según `SettingsManager`.
   - **Resize por arrastre del borde** interior (handle de 10 px) con cursor
     `SizeHorCursor`; emite `widthChanged` para persistir.
   - **Refresh** automático cada 10 minutos + botón manual; descarga en un
     **hilo daemon** y entrega al hilo de la UI vía señal `_itemsFetched`
     (no se tocan widgets desde el hilo de trabajo).
   - **Animación de entrada**: cada tarjeta crece en altura + fade y se
     inserta arriba de la lista (el resto baja), todo a mano en QTimer —
     sin efectos Qt (ADR-001).
   - Clic en una noticia: abre el enlace con `webbrowser.open`.
   - Estado desconectado (`EmptyNewsView`): mensaje + botón CONECTAR que
     emite `configureRequested`.
3. **`ui/settings_dialog.py`** — `SettingsDialog` (rueda ⚙):
   - Apariencia: selector de tema con swatches; activar panel; posición.
   - Fuentes: `ConnectDialog` modal con presets y URL personalizada.
   - La validación de la URL personalizada corre en hilo daemon y el
     resultado vuelve al hilo principal por **señal Qt propia**
     (`validationDone = pyqtSignal(bool, str)`), en lugar de
     `QMetaObject.invokeMethod` con kwargs (API inválida en PyQt6).

## Opciones evaluadas

| Opción | Ventajas | Desventajas | Resultado |
|--------|----------|-------------|-----------|
| Librería feedparser | Parseo robusto de muchos formatos | Dependencia nueva (contra restricción) | Descartada |
| stdlib urllib + ElementTree (elegida) | Cero dependencias, suficiente para RSS/Atom | Formatos exóticos pueden fallar | **Elegida** |
| QThread + worker | Sincronización "estándar" | Más código; hilo daemon + señal cubre el caso | Descartada |
| `QMetaObject.invokeMethod` con kwargs | Sin señal nueva | **API inválida en PyQt6** (crasheaba/errores) | Descartada (bug v1.4) |

## Consecuencias

- **Positivas**: zero-dependency para noticias; el panel respeta las reglas
  de renderizado (0 warnings QPainter verificado); el cruce de hilos es
  seguro (señales Qt, nunca widgets desde hilos de trabajo); la URL
  personalizada se valida sin bloquear la UI.
- **Negativas / notas**: feeds no estándar (JSON Feed, webs mal formadas)
  no se soportan; el tamaño de la lista está acotado (máx. items visibles)
  para evitar saturación visual; `settings.json` persiste fuentes y
  configuración del panel.

## Criterios de aceptación (verificados)

- 18 noticias reales descargadas y ordenadas por fecha (prueba en vivo con
  4 fuentes: El Tiempo, Google News, BBC Mundo, El Espectador).
- Panel construye, redimensiona y captura en offscreen sin errores.
- `ConnectDialog` valida una URL RSS real en hilo sin crash y sin
  `QMetaObject.invokeMethod`.

## Referencias

- Commit: `feat(news): add lateral RSS panel...` (pendiente de crear).
- Release GitHub: `v1.4.0` (propuesta).