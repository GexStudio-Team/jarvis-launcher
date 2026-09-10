# ADR-004: Sistema de temas de color (ThemeManager)

- **Estado**: Aceptado
- **Fecha**: 2026-09-10 (America/Bogota)
- **Versión asociada**: v1.4.0
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode)
- **Tipo**: Feature / configuración visual

## Contexto

El launcher nació con un único fondo obsidiana fijo. Para v1.4 se pidió un
conjunto de temas de color (oscuros y claros) seleccionable desde la interfaz,
con cambio en caliente. Además, las preferencias de interfaz del usuario
(tema, panel de noticias) deben persistir entre sesiones.

El estado previo usaba `config.json` exclusivamente para los modos/apps, sin
lugar para preferencias de UI del usuario (que no son configuración de
aplicaciones).

## Decision

1. **Nuevo módulo `core/themes.py`** con un `Theme` (dataclass congelada) que
   define la paleta completa: fondo, fondo alterno, texto, texto atenuado,
   acento, acento suave, bordes de tarjeta, grid, scan, anillos HUD, flag
   `is_dark` y flag `is_obsidian` (el tema clásico conserva el runtime de
   partículas y el boot "obsidiana").
2. **`core/settings.py`** introduce `SettingsManager`, que persiste las
   preferencias de interfaz en un archivo **separado `settings.json`**
   (excluido de git vía `.gitignore`). `config.json` queda reservado a modos
   y apps.
3. **`ThemeManager`** resuelve el tema por identificador, expone la lista de
   temas disponibles y el helper `rgba(color, alpha)` — el único punto que
   convierte un color hex + alpha en `QColor`, evitando los constructores
   inválidos `QColor("#hex", n)` de Qt6.
4. **8 temas**: obsidiana (clásico), nocturno, crimson, esmeralda, matriz,
   violeta, ámbar, luz y nieve.
5. La UI consume el tema a través de `self._theme` y lo re-aplica en caliente
   con `apply_theme()` (fondos, QSS de botones, overlays, panel de noticias).

## Opciones evaluadas

| Opción | Ventajas | Desventajas | Resultado |
|--------|----------|-------------|-----------|
| Temas hardcodeados en `jarvis_ui.py` | Mínimo código | Anida condiciones por todo el paintEvent, inmantenible | Descartada |
| Paleta centralizada + `ThemeManager` (elegida) | Un único lugar define la paleta; el resto consume datos | Nuevo módulo (costo bajo) | **Elegida** |
| CSS/QSS masivo por tema | Fácil global | No cubre el pintado custom (paintEvent) ni overlays | Descartada |
| Archivo de tema externo (JSON) | Sin tocar código para nuevos temas | Más superficie de validación; sin necesidad real hoy | Diferida |

Para la persistencia se evaluó reutilizar `config.json` (mezcla
configuración de apps con preferencias de UI — descartada) frente a
`settings.json` separado (elegida: separación de responsabilidades y el
`settings.json` no se versiona).

## Consecuencias

- **Positivas**: el tema es un dato, no duplicación de lógica; cambiar de
  tema en caliente es trivial; los temas claros permiten trabajar de día.
- **Negativas / notas**: `settings.json` es local del usuario y no debe
  versionarse (`.gitignore`); agregar un tema nuevo implica extender la
  paleta en `core/themes.py` y validar el contraste en los paints custom.

## Criterios de aceptación (verificados)

- Los 8 temas renderizan en prueba offscreen sin errores QPainter.
- Cambio en caliente (tema → `apply_theme()` → grab) sin excepciones.
- `settings.json` persiste `theme` y es ignorado por git.

## Referencias

- Commit: `feat(themes): add color theme system...` (pendiente de crear).
- Release GitHub: `v1.4.0` (propuesta).