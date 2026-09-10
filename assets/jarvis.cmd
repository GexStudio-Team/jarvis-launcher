@echo off
REM ============================================================
REM  jarvis.cmd - Comando global para abrir el J.A.R.V.I.S.
REM  Launcher desde cualquier CMD o PowerShell.
REM
REM  Instalado en: %USERPROFILE%\bin\jarvis.cmd
REM  Fuente:       assets\jarvis.cmd (repositorio)
REM ============================================================

set "LAUNCHER_DIR=C:\Users\Duvan Altamar\Documents\Proyectos\GexClub\proyectos\jarvis-launcher"
set "PYTHONW=C:\Users\Duvan Altamar\AppData\Local\Programs\Python\Python313\pythonw.exe"

if not exist "%LAUNCHER_DIR%\main.py" (
    echo [JARVIS] Error: no se encontro el launcher en "%LAUNCHER_DIR%".
    echo [JARVIS] Revisa la ruta o reinstala con install_jarvis_cmd.bat.
    pause
    exit /b 1
)

cd /d "%LAUNCHER_DIR%"

REM pythonw: abre la GUI sin ventana de consola y devuelve el prompt
start "" "%PYTHONW%" main.py