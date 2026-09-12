# Proceso de release del J.A.R.V.I.S. Launcher

- **Ámbito**: J.A.R.V.I.S. Launcher (repositorio `GexStudio-Team/jarvis-launcher`,
  visibilidad **pública**).
- **Última actualización**: 2026-09-11 (America/Bogota), v2.0.3.
- **Fuentes**: reglas globales de ingeniería (README/docs/TODO/ADR/CHANGELOG),
  `documentacion-continua`, Disciplina de Documentación Continua.

## 1. Identidad de marca (quién habla y a quién)

| Rol | Quién es | Ejemplo |
|---|---|---|
| **GexStudio Team** | Los desarrolladores (remitente de los mensajes y autor de los cambios) | *"Su equipo GexStudio Team"* |
| **GexClub** | La comunidad / "producto" hogar del ecosistema (destinatario) | *"comunidad GexClub"* |
| **J.A.R.V.I.S.** | Un proyecto de **GexClub**, desarrollado por **GexStudio Team** | El launcher |

Regla de oro en todo mensaje de comunidad y documentación de release:

> No se saluda a "la comunidad de GexStudio". Se saluda a la **comunidad de
> GexClub**; el remitente firma como **GexStudio Team**.

Encabezado estándar de la sección de comunidad en `CHANGELOG.md` y en las
notes de GitHub:

```text
## 🎙️ GexStudio Team → Comunidad GexClub
```

## 2. Saludo con horario real de América/Bogota

El saludo del mensaje de comunidad debe coincidir con la hora real de Bogotá
en el momento de publicar (zona horaria oficial del proyecto). Franjas
(las mismas de `core/greeting.py`):

| Franja (hora de Bogotá) | Saludo |
|---|---|
| 05:00 – 11:59 | Buenos **días** |
| 12:00 – 18:59 | Buenas **tardes** |
| 19:00 – 04:59 | Buenas **noches** |

### 2.1 Verificación automática

```python
from core.version import greeting_for_bogota
print(greeting_for_bogota())   # p. ej. "Buenas noches"
```

El helper existe precisamente para no depender del reloj de la memoria del
agente: **siempre consultar la hora de Bogotá antes de escribir el mensaje**.

## 3. Versión mostrada por el launcher (fuente única)

- La UI lee la versión de `core/version.get_app_version()`, **no** de
  `config.json`.
- `get_app_version()` devuelve el **tag git más reciente**
  (`git describe --tags --abbrev=0`) y cae a la constante `__version__` si el
  entorno no tiene git.
- Consecuencia: **al publicar un tag, la versión mostrada al iniciar cambia
  sola** (sin editar `config.json`).
- En cada release, actualizar la constante `__version__` de `core/version.py`
  (es la versión que verán las instalaciones entregadas sin git).
- `config.json` y el `DEFAULT_CONFIG` de `core/config.py` conservan `version`
  solo como metadato documental (se sincronizan en la misma release).

## 4. Flujo de la release (checklist)

1. **Rama de trabajo** con nombre semántico (`fix/`, `feat/`, `perf/`,
   `docs/`…), commits detallados (qué + por qué) y push.
2. **Abrir PR** con body estructurado (objetivo, contexto, cambios, cómo
   probar, referencias) y **esperar aprobación** del usuario.
3. **Merge** a `main` (`--merge --delete-branch`) y `git pull origin main`.
4. **CHANGELOG**: abrir la sección `[X.Y.Z]` (fecha `America/Bogota`) con
   `### Fixed` / `### Added` / `### Changed` + identificadores de bug (G-NNN)
   cuando aplique, **más** la sección
   `## 🎙️ GexStudio Team → Comunidad GexClub` con el mensaje afianzado:
   - saludo según franja de Bogotá (§2, verificar con `greeting_for_bogota()`);
   - qué se detectó/arregló (fácil de leer, tono cercano pero profesional);
   - cierre cálido con la identidad correcta (§1);
   - e incluir la sección de comunidad SOLO al cerrar la versión (no en
     `[Unreleased]`), o bien escribirla en el release notes y duplicarla en
     CHANGELOG al liberar.
5. **`git add` + commit** (`docs(changelog): cerrar release X.Y.Z`) + push.
6. **Release GitHub**:
   `gh release create vX.Y.Z --title "..." --notes-file notas.md --target main`
   con las notas en `temp/opencode/release_vX_Y_Z_notes.md` (reusables).
7. **Sincronizar versión**: `core/version.py.__version__` + `config.json`
   `version` + `DEFAULT_CONFIG` (core/config.py).
8. **Verificar repos**: `git log --oneline -3`, `gh release list`,
   `git branch -a`, `git fetch --tags --prune`.

## 5. Referencias

- `core/version.py` (fuente de versión + `greeting_for_bogota()`).
- `CHANGELOG.md` (historial con mensajes de comunidad).
- `docs/ADR-009`, `docs/ADR-010`, `docs/ADR-011` (decisiones de rendimiento,
  UX y modo foco total asociadas a releases recientes).
- Reglas globales de ingeniería (skill `reglas-globales-ingenieria`):
  trazabilidad requisito → ADR → commit → PR → release.