# ADR-011: Modo foco total — la ventana principal tapa toda la vista

- **Estado**: Aceptado
- **Fecha**: 2026-09-11 (America/Bogota)
- **Versión asociada**: v2.0.2 (rama `fix/v2-community-bugs`)
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode)
- **Tipo**: UX / comportamiento de ventana

## Contexto

Desde v2.0.0 J.A.R.V.I.S. funciona como "modo foco": frameless, siempre al
frente y ocultado a la bandeja al lanzar apps. Sin embargo, el posicionamiento
inicial usaba una geometría centrada limitada a **1480×920**:

```python
w = min(1480, geo.width() - 60)   # centrado, "flotante"
h = min(920, geo.height() - 60)
```

La comunidad reportó (bug G-002):

> "sigue viéndose como ventana flotante, me tiene que tapar toda la vista"

En la misma jornada de revisión se detectaron dos bugs relacionados de
estabilidad y respuesta de la UI (G-001 y G-003):

1. **G-001 (crash)**: `JarvisUI` era invocada como `self.apply_news_panel()`
   y `hasattr(parent_ui, "apply_news_panel")` desde dos flujos
   (`_open_connect_dialog` y `_apply_and_close`), pero ese método **no
   existía** (el real era `_apply_news_panel_position`). El `AttributeError`
   al aceptar "CONECTAR" o "Aplicar" **cerraba el launcher**.
2. **G-003 (no refresca)**: al aplicar ajustes, el panel no se re-aplicaba ni
   re-descargaba; las noticias solo cambiaban al reiniciar la app.

## Opciones consideradas (dimensionado de ventana)

| Opción | Descripción | Ventajas | Desventajas | Veredicto |
|---|---|---|---|---|
| A. Geometría centrada 1480×920 | Estado actual | Borde respirado; parece app de escritorio | **Flotante**; no tapa la vista | ❌ Rechazada |
| B. `availableGeometry()` | Tapa todo el escritorio salvo la barra de tareas | Tapa la vista útil | Deja la barra de tareas visible (menos "HUD total") | ⚠️ Considerada |
| C. `screen.geometry()` completo | Tapa **absolutamente toda** la pantalla | Total inmersión HUD; frameless + siempre al frente | Ocupa el área de la barra de tareas mientras está visible | ✅ **Elegida** |
| D. `showFullScreen()` nativo | Modo fullscreen de Qt | Gestionado por el sistema | Comportamiento distinto según OS; no aporta más que C con frameless | ❌ Descartada |

Se eligió **C**: con `FramelessWindowHint` + `WindowStaysOnTopHint` (ya
establecidos en v2), `setGeometry(screen.geometry())` logra el HUD total de
forma determinista y sin depender del gestor de ventanas.

## Decision

1. **`_center_on_screen()`** ahora expande la ventana a la geometría completa
   del monitor activo (`QApplication.primaryScreen().geometry()`), sin límites
   de ancho/alto.
2. **Tamaño mínimo relativo a la pantalla**:
   `setMinimumSize(min(1200, w), min(720, h))` — garantiza el fullscreen
   incluso en monitores pequeños (p. ej. 1024×768), que antes se recortaban
   por el mínimo fijo de 1200×720.
3. **API pública de panel (bug G-001)**:
   `apply_news_panel()` pasa a existir como método público de `JarvisUI` y
   delega en `_apply_news_panel_position()`. Con esto, el flujo de conexión
   (`jarvis_ui._open_connect_dialog`) y el diálogo de Ajustes
   (`settings_dialog._apply_and_close`) dejan de lanzar `AttributeError`.
4. **Refresco en vivo (bug G-003)**:
   `settings_dialog._apply_and_close()` invoca además `refresh_news()` sobre el
   padre `JarvisUI` al guardar ajustes; el panel re-descarga las fuentes sin
   reiniciar.

## Consecuencias

- **Positivas**: la ventana tapa toda la vista (modo foco total pedido por la
  comunidad); se elimina el crash al cambiar de fuente (G-001); los ajustes
  de noticias/posición se aplican al instante (G-003); el tamaño mínimo ya no
  rompe en pantallas pequeñas.
- **Negativas**: mientras el launcher está visible ocupa todo el monitor
  (incluida la zona de la barra de tareas); es un cambio de comportamiento
  visual que la comunidad pidió explícitamente.
- **Compatibilidad**: `F11` sigue alternando (fullscreen ↔ normal, que ahora
  también usa la geometría de pantalla); el atajo global y la bandeja no
  cambian; no se modifica la API existente salvo la **adición** del método
  público `apply_news_panel()` (compatible hacia atrás).

## Referencias

- Bugs de comunidad: G-001, G-002, G-003 (CHANGELOG v2.0.2)
- `ui/jarvis_ui.py` (`_center_on_screen`, `apply_news_panel`,
  `setMinimumSize`)
- `ui/settings_dialog.py` (`_apply_and_close`)
- [ADR-006](./ADR-006-atajo-global-bandeja.md) (comportamiento de ventana v2)
- [ADR-007](./ADR-007-lector-noticias.md) (lector a pantalla completa)