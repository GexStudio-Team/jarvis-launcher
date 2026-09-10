@echo off
REM -------------------------------------------------------
REM J.A.R.V.I.S. Launcher - Instalador de Auto-Inicio
REM -------------------------------------------------------
REM Ejecuta este .bat como Administrador para instalar o
REM desactivar el auto-inicio al iniciar Windows.
REM -------------------------------------------------------

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set PROJECT_DIR=%USERPROFILE%\Documents\Default Project\jarvis-launcher
set VBS_TARGET=%STARTUP_DIR%\JarvisLauncher.vbs

if exist "%VBS_TARGET%" (
    echo [JARVIS] Desactivando auto-inicio...
    del "%VBS_TARGET%"
    echo [JARVIS] Auto-inicio DESACTIVADO.
) else (
    echo [JARVIS] Activando auto-inicio...
    (
        echo Set WshShell = CreateObject^("WScript.Shell"^)
        echo WshShell.CurrentDirectory = "%PROJECT_DIR%"
        echo WshShell.Run """python"" ""%PROJECT_DIR%\main.py""", 0, False
    ) > "%VBS_TARGET%"
    echo [JARVIS] Auto-inicio ACTIVADO.
)

echo.
pause
