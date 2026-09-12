# ADR-009: Optimización de rendimiento del navegador embebido

- **Estado**: Aceptado
- **Fecha**: 2026-09-11 (America/Bogota)
- **Versión asociada**: v2.0.1 (rama `perf/reader-webengine`)
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode)
- **Tipo**: Rendimiento / optimización

## Contexto

Tras entregar el lector con mini navegador (ADR-008), el usuario reportó la
experiencia real de uso:

> "hago un click y es muy lento en responder"

Análisis técnico de la causa raíz sobre `ui/news_reader.py`:

1. **Arranque perezoso de Chromium (cold start)**: `QWebEngineView` se
   instanciaba dentro de `_open_reader()` en *el primer clic*. Chromium debe
   lanzar sus procesos (GPU, red, renderer) y levantar el motor en ese
   momento: **300 ms – 1.5 s** de "nada" en el primer uso de la sesión. Las
   aperturas siguientes eran rápidas porque la instancia se conserva
   (`hide()` en vez de destruir), pero el primer clic pagaba todo.
2. **Navegación sin caché eficiente**: el perfil de Chromium no garantizaba
   caché HTTP en disco; assets (imágenes, CSS) se re-descargaban en cada
   visita, incluso de artículos ya vistos.
3. **Carga completa + rastreadores**: cada `setUrl()` descarga la página real
   con analytics, publicidad y JS de terceros que añaden peticiones y bytes
   innecesarios.
4. **Latencia percibida**: fade de entrada de 220 ms + beeps de clic
   (ADR-010) alargaban la sensación de respuesta.

## Opciones consideradas

| Opción | Qué hace | Impacto | Riesgo | Veredicto |
|--------|----------|---------|--------|-----------|
| A. Pre-warm de Chromium tras el boot | Instancia `NewsReaderView` oculto a los ~900 ms del arranque; el primer clic solo navega (`setUrl`) | ⭐⭐⭐ elimina el cold start | Bajo (micro-stutter puntual en segundo plano) | ✅ PBS 1 |
| B. Perfil persistente con caché en disco | `defaultProfile()`: `DiskHttpCache` (100 MB) + ruta estable en `%APPDATA%\JarvisLauncher\WebEngine` | ⭐⭐ re-vistas rápidas | Bajo | ✅ PBS 2 |
| C. Bloqueo de rastreadores/publicidad | `QWebEngineUrlRequestInterceptor` corta peticiones a dominios de ads/analytics | ⭐⭐⭐ páginas más ligeras | Bajo (lista conservadora; no toca CDN de contenido ni imágenes) | ✅ PBS 3 |
| D. Settings de red y reproducción | `DnsPrefetchEnabled` + `PlaybackRequiresUserGesture` (sin autoplay: menos datos) | ⭐ complemento real | Mínimo | ✅ PBS 4 |
| E. Fade de apertura 220 → 110 ms | Respuesta visual casi instantánea al clic | Percibido alto | Nulo | ✅ PBS 5 |
| F. Precargar la página completa en segundo plano al abrir el launcher | `setUrl` de la primera noticia durante el boot | Alto | Medio-alto (consume datos sin pedido, indexa cookies de terceros de un sitio arbitrario) | ❌ Descartada |

**Decisión**: A + B + C + D + E; se descarta F (carga de contenido de terceros
sin consentimiento explícito del clic).

## Decision

### En `ui/news_reader.py`

1. **El view NO navega en el constructor** (antes hacía `setUrl(about:blank)`):
   los procesos de Chromium arrancan *al instanciar* el `QWebEngineView`; la
   navegación real queda exclusivamente en `show_article()` (clic) y
   `prewarm()`. Esto separa "levantar el motor" (barato, controlable) de
   "pedir la web" (costoso, a petición del usuario).
2. **Perfil compartido y cacheado** (`QWebEngineProfile.defaultProfile()`):
   - `HttpCacheType.DiskHttpCache` con máximo **100 MB**;
   - `PersistentCookiesPolicy.ForcePersistentCookies`;
   - `setPersistentStoragePath(%APPDATA%\JarvisLauncher\WebEngine)`.
3. **`_TrackerBlocker(QWebEngineUrlRequestInterceptor)`**: bloquea peticiones a
   17 dominios conocidos de publicidad/análisis (host igual o subdominio).
   Lista deliberadamente conservadora: **no bloquea** CDN de imágenes, CSS ni
   fuentes — solo rastreadores.
4. **Settings del view**: `DnsPrefetchEnabled=True` y
   `PlaybackRequiresUserGesture=True` (el autoplay de video queda prohibido
   hasta gesto del usuario: menos datos y menos carga).
5. `show_article()` usa `QUrl(item.url)` (antes la ruta obtusa
   `engine.url().__class__(item.url)`).
6. **Switch de CI** `JARVIS_DISABLE_WEBENGINE=1`: en entornos headless sin GPU
   el renderer de Chromium crashea al navegar (fail-fast
   `0xC0000409`); con la variable, el lector se prueba completo por el camino
   de fallback de texto, y el motor solo se valida *sin navegar* (constructor
   + settings). **En producción la variable no se define.**

### En `ui/jarvis_ui.py`

7. **`_prewarm_webengine()`** disparado con `QTimer.singleShot(900, ...)`
   después del boot (no al primer clic): crea el `NewsReaderView` oculto
   (y con él el motor Chromium) y lo conserva vía `hide()`.
8. **Fade de apertura reducido a 110 ms** (antes 220 ms).

## Consecuencias

- **Positivas**: el primer clic pasa de "arrancar Chromium + navegar" a solo
  "navegar" (diferencia de cientos de ms a ~1 s); re-vistas y assets repetidos
  salen de caché; las páginas cargan con menos rastreadores; la respuesta
  visual es instantánea.
- **Negativas**: Chromium queda residente en segundo plano tras el boot
  (un proceso hijo ~40–80 MB más; mismo coste que teníamos al abrir el lector,
  ahora adelantado). Aceptable por la ganancia de UX.
- **CI**: los tests headless validan la lógica completa por fallback y el motor
  solo en creación/configuración; **la validación de velocidad real (clic →
  página cargada) se hace en Windows con GPU** (plantilla de prueba manual en
  TODO.md).
- **Pruebas**: `test_reader_v2.py` (fallback completo), `test_engine_warm.py`
  (constructor + settings + bloqueador por unidad), integración con `JarvisUI`,
  boot y render — **0 errores** en offscreen.

## Actualización v2.0.2 (G-004 / G-005)

La comunidad reportó que "las noticias cargan muy lento" y que "cambiar de
una a otra se demora en renderizar". Se extiende la optimización en dos frentes:

1. **Descarga de fuentes en paralelo (G-004)**: `NewsService.fetch_sources`
   usa `ThreadPoolExecutor` (máx. 6 workers) en lugar del bucle secuencial.
   Urllib libera el GIL durante el I/O de red, por lo que el paralelismo es
   real: el tiempo total pasa de `Σ latencias` a `≈ máx`. Medido en offscreen:
   12 fuentes que fallan rápido ≈ **2.1 s**. Fuentes duplicadas por URL se
   descargan una sola vez; el caché de 600 s por fuente se conserva bajo
   `ThreadPoolExecutor` (acceso atómico de dict bajo GIL).
2. **Cambio de artículo instantáneo (G-005)** — patrón *resumen primero,
   web después*: `MiniBrowser.show_article()` ya no bloquea el render esperando
   la navegación real; muestra de inmediato el resumen del feed (HTML local
   con tipografía del tema, ~1 ms) y dispara `setUrl()` en segundo plano.
   Un `loadFinished` propio (`_on_web_finished`) con guard por secuencia
   (`_load_seq`) cambia al `QWebEngineView` cuando la página termina — si el
   usuario cambió de artículo mientras cargaba, la web de la carga antigua no
   se muestra. Si el artículo ya estaba cargado (misma URL), se muestra la web
   directa sin re-descargar.

Consecuencias v2.0.2: la primera carga del panel es ~la más lenta de las
fuentes (no la suma); navegar entre artículos es instantáneo a la percepción
y la web completa llega sola por detrás. Estabilidad: `ThreadPoolExecutor`
entra como en por contexto (espera a todos los hilos al salir), sin pérdida
de items y con el mismo dedup/orden por fecha.

## Referencias

- [ADR-008](./ADR-008-webengine.md) (mini navegador, decisión original)
- [ADR-001](./ADR-001-quitar-qgraphicseffect.md) (sin `QGraphicsEffect`; fades
  con `windowOpacity` nativa)
- [ADR-010](./ADR-010-feedback-sin-sonido.md) (eliminación de los beeps)
- [ADR-011](./ADR-011-modo-foco-total.md) (modo foco total v2.0.2)
- `ui/news_reader.py`, `ui/jarvis_ui.py`, `core/news.py`