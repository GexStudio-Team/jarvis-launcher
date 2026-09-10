# Changelog

Todos los cambios notables en el J.A.R.V.I.S. Launcher.

Formato basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [1.3.0] - 2026-09-10 (America/Bogota)

### Added
- Comando global `jarvis`: `assets/jarvis.cmd` + instalador `install_jarvis_cmd.bat`
  que copia el script a `%USERPROFILE%\bin` y lo agrega al PATH de usuario
- Se abre cualquier ventana nueva de CMD o PowerShell y se escribe `jarvis`
  para lanzar el launcher (usa `pythonw.exe`, sin consola y devuelve el prompt)

### Fixed
- El comando resuelve correctamente desde PowerShell y CMD (verificado con
  reconstruccion del PATH desde el registro y lanzamiento real del proceso)

---

## [1.2.0] - 2026-09-10 (America/Bogota)

### Fixed
- Conflictos de QPainter (`paint device can only be painted by one painter`): se eliminaron todos los `QGraphicsEffect` (opacity en la ventana, drop shadow en las tarjetas) que, combinados con `paintEvent` custom, generaban spam de errores y tarjetas pintadas en negro al hacer hover en Qt6
- Fade-in de la ventana ahora usa la propiedad nativa `windowOpacity` en lugar de `QGraphicsOpacityEffect`
- Overlays (boot y flash) ahora animan su opacidad con propiedades propias (`fade`/`alpha`) y repintado manual
- Sonidos de feedback: reemplazado `PlaySound(SND_ALIAS)` (dependia del esquema de sonido de Windows) por `winsound.Beep` con frecuencias reales en hilos daemon
- `core/launcher.py`: resolucion robusta de rutas de apps (PATH, menu de inicio `.lnk` via COM y registro App Paths); mensaje claro cuando la app no esta instalada
- `config.json`: las apps Discord y Spotify ahora usan nombre corto (`"Discord"`, `"Spotify"`) en lugar de rutas fijas que cambiaban con cada instalacion

### Added
- Beam de energia desde el nucleo central hacia la tarjeta seleccionada (efecto HUD animado)
- Corner brackets estilo mira/arqueria en las tarjetas (se acentuan en hover)
- Halo exterior de hover dibujado manualmente (reemplaza al `QGraphicsDropShadowEffect`)
- Pantalla de boot rediseñada: barra de progreso animada, titulo con glow medido por font metrics y posiciones dinamicas

### Changed
- `ui/mode_card.py`: sin `QGraphicsDropShadowEffect`, todo el glow se dibuja en `paintEvent`
- Boot overlay centrado dinamicamente segun el ancho real del texto

---

## [1.1.0] - 2026-09-09 (America/Bogota)

### Fixed
- Error `ImportError: QDesktopWidget` en PyQt6: reemplazado por `QApplication.primaryScreen().availableGeometry()`
- Fuga del lock de instancia unica: el socket ahora se retiene globalmente y no usa SO_REUSEADDR
- Limpieza del handler de seleccion de modo en `main.py` (sin ui=None provisional)

### Added
- `core/state.py`: historial de modos recientes persistente (`state.json`)
- `core/feedback.py`: sonidos de feedback con winsound (click, exito, error)
- `core/notifier.py`: notificaciones toast nativas de Windows via PowerShell
- Pantalla de boot animada tipo arranque de sistema
- Efecto typewriter en el greeting
- Flash de color del modo al seleccionar + pulse de tarjeta al click
- Barra de estado muestra el ultimo modo usado y hace cuanto
- Soporte multi-monitor (centrado en monitor primario)

---

## [1.0.1] - 2026-09-09 (America/Bogota)

### Added
- `.gitignore` para excluir `__pycache__`, entornos virtuales y archivos de IDE
- Repositorio publico: https://github.com/GexStudio-Team/jarvis-launcher
- Proyecto movido a `Documents/Proyectos/GexClub/proyectos/jarvis-launcher`

---

## [1.0.0] - 2026-09-09 (America/Bogota)

### Added
- Interfaz principal tipo JARVIS con efectos HUD completos (anillos rotantes, particulas, scan line, vignette)
- 3 modos de operacion: Gaming, Trabajo, Estudio
- Tarjetas animadas con efecto glassmorphism, hover glow y elevacion
- Motor de lanzamiento de aplicaciones con soporte para ejecutables, argumentos y URLs
- Configuracion via `config.json` (JSON editable)
- Auto-inicio en Windows con script VBS (oculta consola)
- Boton de toggle auto-inicio desde la interfaz
- Deteccion de instancia unica (puerto local)
- Lanzamiento de apps en hilo separado para no bloquear la UI
- Atajos de teclado: Escape (cerrar), F11 (fullscreen)
- Documentacion completa: README, CHANGELOG, TODO
