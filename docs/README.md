# Documentación técnica - J.A.R.V.I.S. Launcher

Fuente principal de documentación técnica y operativa para desarrolladores.
La documentación de usuario (qué es y cómo usarlo) vive en el
[README.md raíz](../README.md).

## Índice

| Documento | Contenido |
|-----------|-----------|
| [Arquitectura.md](./Arquitectura.md) | Componentes, módulos, responsabilidades, flujo de información, operaciones, TODOs y deuda técnica |
| [ADR-001-quitar-qgraphicseffect.md](./ADR-001-quitar-qgraphicseffect.md) | Decisión: eliminar `QGraphicsEffect` y pintar efectos manualmente (v1.2.0) |
| [ADR-002-resolucion-apps-por-nombre.md](./ADR-002-resolucion-apps-por-nombre.md) | Decisión: resolución de rutas de apps por nombre (v1.2.0) |
| [ADR-003-comando-global-jarvis.md](./ADR-003-comando-global-jarvis.md) | Decisión: comando global `jarvis` para lanzar la app desde CMD/PowerShell (v1.3.0) |

## Convenciones

- Tonos: formal, técnico y profesional en todos los `.md` de producción.
- Marcas de tiempo en zona horaria `America/Bogota`.
- Los ADRs se numeran de forma secuencial y no se modifican silenciosamente;
  si una decisión deja de ser válida, se registra un ADR nuevo o se actualiza
  su estado con justificación.
- Las decisiones arquitectónicas importantes SIEMPRE se documentan como ADR.