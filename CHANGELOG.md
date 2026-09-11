# Changelog

Todos los cambios notables en el J.A.R.V.I.S. Launcher.

Formato basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- `ui/news_reader.py` (`NewsReaderView`): **lector de noticias a pantalla
  completa** (spec v2 puntos 3 y 4) que se abre al hacer clic en una noticia
  del panel:
  - **Split-pane redimensionable** (`QSplitter`, estilo `QSplitter::handle`)
    con lista compacta a la izquierda (título + fuente/hora, artículo actual
    resaltado) y lectura larga a la derecha
  - **Tipografía de lectura larga**: columna centrada (~760 px), título en
    Georgia 26 px, meta fuente·hora en dim, **lead destacado con capitular**
    (primera letra en acento), **pull-quote** del resumen en cursiva con barra
    lateral de acento y divisores tipográficos
  - **Contenido del feed** (`extra["summary"]`) dividido en lead / cita / cuerpo
    con `_split_readable()`; cuando el feed no trae resumen, muestra un aviso
    y el botón **"Abrir original ↗"** (navegador) queda como camino principal
  - Navegación por teclado: `←`/`→` cambian de artículo y `Escape` vuelve al
    launcher; click en la lista también navega; fade de entrada con
    `windowOpacity` (sin `QGraphicsEffect`, ADR-001)

### Changed
- `ui/news_panel.py`: el clic en una noticia ahora emite
  `readerRequested(items, index)` y **abre el lector** (`NewsReaderView`)
  en lugar de saltar directamente al navegador (el enlace original sigue
  disponible dentro del lector); se mantiene `configureRequested` para el
  conector de fuentes y se elimina el uso de `webbrowser` en el panel
- `ui/jarvis_ui.py`: integra `NewsReaderView` bajo demanda
  (`_open_reader` / `_close_reader`), conecta `readerRequested`, prioriza los
  atajos del lector en `keyPressEvent` y aplica el tema vivo al abrir

### Docs
- `docs/ADR-007-lector-noticias.md` (decisión del lector: split-pane + contenido
  del feed + "Abrir original"); `docs/Arquitectura.md` y `README.md`
  actualizados con el nuevo módulo y flujo

---

## [2.0.0] - 2026-09-11 (America/Bogota)

### Added
- `core/hotkey.py` (`GlobalHotkey`): atajo global `Ctrl+Shift+Espacio` para
  convocar/ocultar el launcher desde cualquier aplicación, implementado con
  `RegisterHotKey` (API nativa de Windows vía ctypes) y
  `QAbstractNativeEventFilter`; degradación silenciosa si el atajo está en uso
- `core/tray.py` (`Tray`): bandeja del sistema con icono generado por código
  (`QPainter`, sin assets externos), menú contextual Mostrar/Salir y doble
  clic para invocar el launcher
- `core/greeting.py`: saludo dinámico según franja horaria (Buenos días /
  Buenas tardes / Buenas noches) + adjetivo profesional rotativo por arranque
  (Desarrollador, Ingeniero, Arquitecto, Creador, Hacker, Explorador, Maestro,
  Visionario, Estratega, Artesano)
- `core/github_link.py`: vinculación real de la cuenta de GitHub para que el
  launcher salude por el nombre real — detección automática con `gh` autenticado
  (`gh api user`) y verificación manual contra la API pública
  `GET https://api.github.com/users/{username}`; sin tokens ni secretos
- `core/settings.py`: nuevas claves de ajuste con migración suave —
  `tray.enabled`, `github.{username,name}` y `greeting.adjective_index`
- `ui/settings_dialog.py` (`GithubDialog`): modal de vinculación de cuenta
  GitHub con detección automática en hilo y verificación manual por username
- Opción 5 “Próximamente” en el panel de control: editor visual de modos,
  editor de paletas y lector de noticias a pantalla completa (estado borrador)

### Changed
- **Comportamiento de ventana (decisión C del diseño v2)**: el launcher queda
  SIEMPRE al frente (`show_and_raise` + `activateWindow`), se oculta
  automáticamente al elegir un modo (deja al frente las aplicaciones lanzadas)
  y se reinvoca con el atajo global o la bandeja; el botón ✕ ahora oculta a la
  bandeja en lugar de cerrar la aplicación
- `ui/mode_card.py`: rediseño "modo workspace" — el icono emoji flotante se
  sustituye por un monograma tipográfico (inicial del modo) en contenedor
  sobrio, barra de acento superior estilo IDE, paleta del tema, jerarquía clara
  (nombre / descripción / contador de aplicaciones en Consolas); se CONSERVAN
  los modos Gaming/Trabajo/Estudio tal como pidió el usuario
- `ui/news_panel.py`: cabecera nueva "¿QUÉ ESTÁ PASANDO EN EL MUNDO AHORA?",
  items con jerarquía tipográfica limpia (fuente + hora en dim, título
  destacado de 2 líneas, preview del resumen del feed), estado vacío sobrio sin
  emoji grande y botón CONFIG de fuentes
- `ui/settings_dialog.py`: el panel de control pasa a ser una LISTA
  ESTRUCTURADA con filas etiqueta-izquierda/control-derecha y separadores
  (1 · Apariencia, 2 · Comportamiento, 3 · Noticias, 4 · Cuenta de GitHub,
  5 · Próximamente); añadidos controles de bandeja y auto-inicio funcionales
- `ui/jarvis_ui.py`: integración de bandeja + atajo global + saludo dinámico;
  `refresh_greeting()` y `toggle_startup()` públicos para el diálogo de ajustes;
  el icono de bandeja se recolorea al cambiar de tema
- `main.py`: usa `show_and_raise()` al arrancar y detecta automáticamente la
  cuenta GitHub en un hilo si aún no está vinculada

### Fixed
- El launcher podía quedar detrás de otras ventanas al arrancar: ahora fuerza
  z-order y foco con `raise_()` + `activateWindow()`

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
