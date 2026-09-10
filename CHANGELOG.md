# Changelog

Todos los cambios notables en el J.A.R.V.I.S. Launcher.

Formato basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [1.4.0] - 2026-09-10 (America/Bogota)

### Added
- `core/settings.py` (`SettingsManager`): preferencias de interfaz del usuario
  en `settings.json` separado de `config.json` (tema, estado/posición/ancho del
  panel de noticias y fuentes RSS); `settings.json` excluido de git
- `core/themes.py` (`Theme` + `ThemeManager`): sistema de temas de color con 8
  paletas (obsidiana, nocturno, crimson, esmeralda, matriz, violeta, ambar,
  luz, nieve) y helper `rgba()` para construir `QColor` con alpha
- `core/news.py` (`NewsService`): descarga/parseo de feeds RSS 2.0 y Atom con
  solo la biblioteca estándar (sin dependencias nuevas); 10 fuentes
  predefinidas + URL RSS/Atom personalizada; fechas normalizadas a UTC aware
- `ui/news_panel.py` (`NewsPanel`): panel lateral de noticias con posición
  izquierda/derecha, ancho redimensionable por el borde (280–560 px), refresh
  automático cada 10 min, descarga en hilo separado (señal a la UI),
  animación de entrada por tarjeta y apertura de la noticia en el navegador al
  hacer clic; estado desconectado con botón CONECTAR
- `ui/settings_dialog.py` (`SettingsDialog`): rueda ⚙ con selector de tema
  (swatches), activación y posición del panel de noticias; `ConnectDialog`
  modal con presets y URL personalizada con validación en hilo
- `ui/mode_card.py`: tarjeta con pintura 100% custom, icono flotante animado,
  zoom en hover, sweep de selección, brackets de esquina y entrada escalonada
- `ui/jarvis_ui.py`: layout compacto sin huecos grandes (barra superior,
  título, tarjetas, estado y panel lateral), temas en caliente en todos los
  fondos HUD, rueda de ajustes integrada
- Docs: `docs/ADR-004-temas-thememanager.md` y
  `docs/ADR-005-panel-noticias-rss.md`; `docs/Arquitectura.md` actualizada con
  los nuevos módulos y flujos

### Fixed
- Crash nativo al iniciar en Qt6 por constructores inválidos
  `QColor("#hex", alpha)` en overlays y grid (reemplazados por
  `ThemeManager.rgba`)
- `ConnectDialog`: la validación de URL usaba `QMetaObject.invokeMethod` con
  kwargs (API inválida en PyQt6); se reemplazó por la señal Qt propia
  `validationDone(bool, str)` con entrega segura al hilo principal

### Changed
- `ui/mode_card.py` dejó de usar sub-widgets para el contenido: todo el estado
  visual se pinta en `paintEvent` (más liviano y sin conflictos de painter)
- `main.py` ahora inyecta `SettingsManager` a `JarvisUI`
- `.gitignore` excluye `settings.json` (preferencias locales del usuario)

---

## [Unreleased]

### Added
- Carpeta `docs/` como fuente principal de documentación técnica:
  - `docs/Arquitectura.md`: componentes, módulos, flujo de información, operaciones y deuda técnica
  - `docs/ADR-001-quitar-qgraphicseffect.md`: decisión de eliminar `QGraphicsEffect` y pintar efectos manualmente (v1.2.0)
  - `docs/ADR-002-resolucion-apps-por-nombre.md`: decisión de resolución de rutas por nombre corto (v1.2.0)
  - `docs/ADR-003-comando-global-jarvis.md`: decisión del comando global `jarvis` (v1.3.0)
- Enlace a `docs/` desde el README raíz (documentación técnica separada de la de usuario)

### Changed
- README raíz ahora se declara explícitamente como documentación de usuario final

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
