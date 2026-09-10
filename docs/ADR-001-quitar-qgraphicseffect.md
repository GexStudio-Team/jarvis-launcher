# ADR-001: Eliminar QGraphicsEffect y pintar efectos manualmente

- **Estado**: Aceptado (retrospectivo)
- **Fecha**: 2026-09-10 (America/Bogota)
- **Versión asociada**: v1.2.0
- **Decisores**: Duvan Altamar (usuario), Technical Partner (openode)
- **Tipo**: Rendimiento / corrección de renderizado

## Contexto

En Qt 6 (`PyQt6`), los widgets que sobreescriben `paintEvent` y además usan
`QGraphicsEffect` (sombra, opacidad) presentan dos problemas:

1. **Spam de warnings de QPainter** en consola ("QPainter::begin() returned
   false"/"Painter not active") y pérdida de rendimiento por repintados
   redundantes.
2. **Tarjetas negras al pasar el ratón (hover)**: el efecto se combina mal con
   el `paintEvent` personalizado y degrada el frame con el backdrop, dejando
   el contenido negro.

El código anterior de `ui/jarvis_ui.py` y `ui/mode_card.py` combinaba
`QGraphicsDropShadowEffect`, `QGraphicsOpacityEffect` con pintura manual
personalizada en cada frame de animación → condiciones de carrera del painter.

## Decision

Eliminar **todos** los `QGraphicsEffect` y reproducir el "estilo" manualmente en
el propio `paintEvent`:

- `ModeCard`: halo de hover con `QRadialGradient` + `QPen`/`QBrush`, highlight de
  selección y brackets de esquina HUD pintados directamente.
- `JarvisUI`: transiciones de opacidad mediante `setWindowOpacity()` (función
  nativa del window) animada con `QPropertyAnimation`; boot/beam/flash pintados
  paso a paso en cada `paintEvent` con propiedades custom (`fade`, `alpha`).

`QGraphicsEffect` queda **prohibido** en este proyecto (ver sección Consecuencias).

## Opciones evaluadas

| Opción | Ventajas | Desventajas | Resultado |
|--------|----------|-------------|-----------|
| Mantener `QGraphicsEffect` | Ninguna detección en ejecución | Warnings QPainter, tarjetas negras, rendimiento pobre | Descartada |
| Pintado manual (elegida) | Control total, sin efectos fantasma, código simple y predecible | Más líneas de pintado (no aplicable a proyectos complejos con sombras reales) | **Elegida** |
| Migrar a QML | Sombras nativas y efectos modernos | Migración completa de UI, curva de aprendizaje, mayor riesgo | Diferida (posible futuro) |

## Consecuencias

- **Positivas**: renderizado estable (0 warnings de QPainter en prueba de
  boot/hover/click), tarjetas siempre visibles, animaciones fluidas.
- **Negativas / limitaciones**: las sombras difusas complejas (blur real)
  requieren código adicional; la estética depende de degradados radiales.
- Para efectos de desenfoque reales a futuro, evaluar QML o `QGraphicsView`
  separado (decisión nueva, con su propio ADR si procede).

## Criterios de aceptación (verificados)

- Prueba de render simulada (boot, hover, click) con **0 warnings de QPainter**.
- Capturas de pantalla generadas en `temp/opencode` (boot, hover, click).
- La aplicación arranca y cierra sin errores.

## Referencias

- Commit: `6ec240a` (fix(ui): eliminar QGraphicsEffect y pintar efectos manualmente).
- Release GitHub: `v1.2.0`.