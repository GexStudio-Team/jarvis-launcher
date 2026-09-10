@echo off
REM ============================================================
REM  install_jarvis_cmd.bat - Instala/uninstala el comando global
REM  `jarvis` en el PATH de usuario (CMD y PowerShell).
REM
REM  Instala:
REM    1. Copia assets\jarvis.cmd  ->  %USERPROFILE%\bin\jarvis.cmd
REM    2. Agrega %USERPROFILE%\bin al PATH de USUARIO (persistente)
REM
REM  Desinstala:
REM    automar.bat con argumento: --uninstall
REM ============================================================

setlocal enabledelayedexpansion

set "BIN_DIR=%USERPROFILE%\bin"
set "BAT_SRC=%~dp0assets\jarvis.cmd"
set "BAT_DST=%BIN_DIR%\jarvis.cmd"

echo.
echo ============================================
echo   J.A.R.V.I.S. Launcher - instalador global
echo ============================================
echo.

if /i "%~1"=="--uninstall" goto uninstall

REM ---- Instalar ----
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

if not exist "%BAT_SRC%" (
    echo [ERROR] No se encontro assets\jarvis.cmd junto a este script.
    exit /b 1
)

copy /Y "%BAT_SRC%" "%BAT_DST%" >nul
echo [OK] Script copiado a: %BAT_DST%

REM ---- Agregar al PATH de usuario si falta ----
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$bin = '%USERPROFILE%\bin';" ^
    "$user = [Environment]::GetEnvironmentVariable('Path','User');" ^
    "if ($user -notlike ('*' + $bin + '*')) {" ^
    "   $new = ($user.TrimEnd(';') + ';' + $bin);" ^
    "   [Environment]::SetEnvironmentVariable('Path', $new, 'User');" ^
    "   Write-Host '[OK] PATH de usuario actualizado con: ' $bin" ^
    "} else {" ^
    "   Write-Host '[=] El PATH ya contenia la carpeta bin'" ^
    "}"

echo.
echo [LISTO] Ahora abre una ventana NUEVA de CMD o PowerShell
echo         y escribe:   jarvis
echo.
pause
exit /b 0

:uninstall
REM ---- Desinstalar ----
if exist "%BAT_DST%" del "%BAT_DST%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$bin = '%USERPROFILE%\bin';" ^
    "$user = [Environment]::GetEnvironmentVariable('Path','User');" ^
    "$parts = @($user -split ';' | Where-Object { $_ -and ($_ -ne $bin) });" ^
    "$new = $parts -join ';';" ^
    "[Environment]::SetEnvironmentVariable('Path', $new, 'User');" ^
    "Write-Host '[OK] Comando jarvis eliminado del PATH de usuario'"

echo.
echo [LISTO] Comando jarvis desinstalado.
echo.
pause
exit /b 0