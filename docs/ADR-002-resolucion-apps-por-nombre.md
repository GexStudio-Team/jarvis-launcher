# ADR-002: Resolución de rutas de aplicaciones por nombre corto

- **Estado**: Aceptado (retrospectivo)
- **Fecha**: 2026-09-10 (America/Bogota)
- **Versión asociada**: v1.2.0
- **Decisores**: Duvan Altamar (usuario), Technical Partner (openode)
- **Tipo**: Confiabilidad / mantenibilidad de configuración

## Contexto

`config.json` almacenaba rutas absolutas fijas a ejecutables (p. ej.
`C:\...\Discord.exe`, `C:\...\Spotify.exe`). Problemas observados:

1. **Rutas cambian** entre instalaciones, versiones o máquinas → el launcher
   "no encuentra" la app y falla en silencio.
2. En la máquina del usuario, **Discord y Spotify no están instalados** como
   ejecutables; sobrevivía solo la carpeta `User Data` → rutas rotas.

Se necesitaba un mecanismo que encontrara la app aunque no se conozca su ruta
exacta, y que funcionara para ejecutables del PATH, accesos directos del Menú
Inicio y entradas de registro estándar de Windows.

## Decision

Adoptar un modelo de **resolución dinámica por nombre corto** en
`core/launcher.py`:

1. **Ruta directa** (`launch_command`) si el archivo existe en disco.
2. **`shutil.which(nombre)`** para ejecutables del PATH del sistema.
3. **Acceso directo `.lnk` del Menú Inicio** (usuario y común) resuelto con
   PowerShell + COM (Shell.Application).
4. **Registro `App Paths`** de Windows (HKCU y HKLM).

El nombre corto se guarda en `config.json` (p. ej. `"Discord"`, `"Spotify"`)
y solo se usa ruta explícita cuando es fiable (Steam, Chrome, VS Code).

Soporta además archivos (`os.startfile`), ejecutables (comillas **SAFE** si la
ruta tiene espacios) y URLs (`http://`/`https://`).

## Opciones evaluadas

| Opción | Ventajas | Desventajas | Resultado |
|--------|----------|-------------|-----------|
| Mantener rutas absolutas fijas | Simple | Frágil ante cambios; experiencias rotas | Descartada |
| Editor manual de rutas en la UI | Control explícito | Más UI, más trabajo de mantenimiento | Diferida |
| Resolución por nombre (elegida) | Resiliente; funciona sin conocer la ruta; cubre PATH, .lnk y registro | Cobertura depende de instaladores estándar; apps portables requieren ruta explícita | **Elegida** |
| Escanear todo el disco | Todas las apps | Lentísimo y frágil | Descartada |

## Consecuencias

- **Positivas**: `config.json` más corto y portable; el usuario puede
  editar apps añadiendo solo el nombre corto; la app tolera reinstalaciones.
- **Negativas**: es una heurística: si una app portable no está en PATH ni en
  Menú Inicio ni en el registro, hay que fijar `launch_command` (uso mixto).
- Si una app no se resuelve, se notifica el nombre (toast + feedback de error)
  en lugar de fallar silenciosamente.

## Criterios de aceptación

- Resolución verificada con Steam (ruta real), Chrome y VS Code (PATH/Start Menu)
  y Discord/Spotify (nombres cortos; se resuelven si existen).
- Lanzamiento real de una app en prueba manual.

## Referencias

- Commit: `6ec240a` (fix(ui): eliminar QGraphicsEffect… incluye launcher.py).
- Módulo: `core/launcher.py`.
- Release GitHub: `v1.2.0`.