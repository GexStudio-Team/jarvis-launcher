# ADR-010: Eliminación del feedback sonoro (beeps de clic)

- **Estado**: Aceptado
- **Fecha**: 2026-09-11 (America/Bogota)
- **Versión asociada**: v2.0.1 (rama `perf/reader-webengine`)
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode)
- **Tipo**: UX / accesibilidad

## Contexto

El launcher reproducía sonidos con `winsound.Beep` (`core/feedback.py`:
`play_click`, `play_success`, `play_error`, `play_cancel`) en 15 puntos de la
UI (cards de modo, panel de noticias, lector, Ajustes). El usuario pidió:

> "quiero quitar los sonidos al hacer un click en algo"

Análisis técnico del coste de mantenerlos:

1. **Molestia real para la comunidad**: `winsound.Beep` usa el *altavoz
   interno* (PC speaker) del sistema; suena distinto del feedback de las apps
   modernas y no era configurable por el usuario.
2. **Sobrecarga por clic**: cada `play_click()` **creaba un hilo daemon**
   (`threading.Thread(target=Beep)`), es decir ~1 hilo por interacción;
   innecesario en una app cuyo feedback correcto es visual.
3. **Latencia percibida**: los tonos (60–260 ms) competían con la respuesta
   visual del clic — junto a fades largos, alargaban la sensación de lentitud
   (ver ADR-009).
4. **Alternativa descartada**: hacerlo configurable (interruptor "Sonidos en
   Ajustes") añade superficie de ajustes y estado para un requisito que la
   comunidad no pidió; se registra como futura feature en TODO.md si algún día
   se solicita explícitamente.

## Decision

1. **Eliminar `core/feedback.py`** (módulo completo) y sus 15 llamadas en
   `ui/jarvis_ui.py`, `ui/news_panel.py`, `ui/news_reader.py` y
   `ui/settings_dialog.py`.
2. **El feedback de la UI queda 100 % visual** (ya existente y suficiente):
   - hover/zoom en cards (`mode_card.py`), sweep de selección y brackets;
   - resaltado del item activo y colores de acento en panel y lector;
   - estado en la barra inferior ("MODO SELECCIONADO — INICIANDO...",
     "SISTEMA LISTO", "Cargando artículo…") y notificaciones de sistema
     (`core/notifier.py`) al completar/cancelar un lanzamiento.
3. No se crea ningún estado nuevo de configuración (cero superficie nueva).

## Consecuencias

- **Positivas**: experiencia más silenciosa y profesional; se eliminan ~1 hilo
  por clic (menos overhead); la app depende solo de feedback visual coherente
  con el diseño HUD; menos código (~54 líneas y 15 puntos de invocación).
- **Negativas**: sin señal sonora en lanzamientos completados (el `Beep` de
  éxito desaparece). Mitigación: la notificación del sistema y la barra de
  estado cubren ese momento.
- **Compatibilidad**: los CHANGELOG de v1.x documentan la historia del sonido;
  se conservan como registro. La estructura de docs se actualiza para reflejar
  el nuevo estado (README, Arquitectura, TODO).

## Referencias

- [ADR-009](./ADR-009-optimizacion-webengine.md) (percepción de lentitud)
- `core/feedback.py` (eliminado), `ui/jarvis_ui.py`, `ui/news_panel.py`,
  `ui/news_reader.py`, `ui/settings_dialog.py`
- Notificaciones visuales: `core/notifier.py`