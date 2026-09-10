# ADR-003: Comando global `jarvis` para lanzar la aplicación

- **Estado**: Aceptado (retrospectivo)
- **Fecha**: 2026-09-10 (America/Bogota)
- **Versión asociada**: v1.3.0
- **Decisores**: Duvan Altamar (usuario), Technical Partner (openode)
- **Tipo**: Distribución / experiencia de usuario (instalación)

## Contexto

La aplicación solo se ejecutaba con:

```powershell
python main.py            # o
pythonw main.py           # sin consola
```

desde la carpeta del proyecto. El usuario necesitaba un comando global
llamado `jarvis` disponible en **cualquier** CMD/PowerShell, sin tener que
navegar a la ruta del proyecto ni escribir `python/pythonw`.

## Decision

Crear y distribuir un **comando global `jarvis`** para Windows:

1. **`assets/jarvis.cmd`**: script de arranque que localiza el `pythonw.exe`
   (versión de Python del sistema, o `py -3` como fallback), ejecuta
   `main.py` **desde el directorio raíz del proyecto** y conserva el prompt
   en la consola.
2. **`install_jarvis_cmd.bat`**:
   - Instala: copia `jarvis.cmd` a `%USERPROFILE%\bin\` y agrega
     `%USERPROFILE%\bin` al **PATH de usuario** (vía `[Environment]::`
     `SetEnvironmentVariable`, persistente, sin elevación de administrador).
   - Desinstala: borra el archivo y quita la entrada del PATH
     (`--uninstall`).

Esta ruta de instalación no requiere permisos de Administrador y no contamina
el PATH del sistema.

## Opciones evaluadas

| Opción | Ventajas | Desventajas | Resultado |
|--------|----------|-------------|-----------|
| Alias manual `doskey` | Rápido | Solo sesión actual; no persiste ni se distribuye | Descartada |
| Instalar en PATH de sistema (System32) | Disponible para todos los usuarios | Requiere administrador; contaminación global | Descartada |
| Carpta `%USERPROFILE%\bin` + PATH de usuario (elegida) | Sin admin; persistente; aislada por usuario; fácil de desinstalar | Solo para el usuario actual | **Elegida** |
| Instalador MSI / wheel de Python | Instalación estándar | Exceso de empaquetado para esta app; más complejo | Diferida |

## Consecuencias

- **Positivas**: `jarvis` + Enter lanza la app desde cualquier terminal;
  desinstalación simple y reversible (`jarvis.cmd` y PATH sin residuos).
- **Negativas**: el PATH de usuario debe ser recargado en consolas abiertas
  (abrir terminal nueva tras instalar); solo afecta al usuario actual.
- **Riesgo de conflictos**: si existe otro `jarvis` en el PATH, gana el que
  aparezca primero; se documenta que `jarvis` resuelve a este script.

## Criterios de aceptación (verificados)

- `jarvis` resuelto desde el registro del PATH de usuario
  (verificación: `RESUELTO: C:\Users\Duvan Altamar\bin\jarvis.cmd`).
- Lanzamiento real: proceso `pythonw.exe` de la aplicación corriendo tras
  ejecutar `jarvis`.
- Desinstalación probada lógicamente (parámetro `--uninstall` elimina la
  entrada y el archivo).

## Referencias

- Commits: `88c47d0` (feat: comando global jarvis + instalador).
- Release GitHub: `v1.3.0`.