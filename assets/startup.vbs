' assets/startup.vbs
' -------------------------------------------------------
' J.A.R.V.I.S. Launcher - Script de auto-inicio Windows
' -------------------------------------------------------
' Ejecuta main.py ocultando la ventana de consola.
' Este archivo se coloca en:
'   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
'
' Para desactivar: simplemente elimina este archivo.
' -------------------------------------------------------

Set WshShell = CreateObject("WScript.Shell")

' Ruta al directorio del proyecto (ajustar si es necesario)
projectDir = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\Documents\Default Project\jarvis-launcher"

' Detectar Python
pythonCmd = "python"

' Ejecutar main.py en segundo plano (ventana oculta)
WshShell.CurrentDirectory = projectDir
WshShell.Run """" & pythonCmd & """ """ & projectDir & "\main.py""", 0, False
