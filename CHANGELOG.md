# Changelog

Todos los cambios notables en el J.A.R.V.I.S. Launcher.

Formato basado en [Keep a Changelog](https://keepachangelog.com/).

---

## [2.0.1] - 2026-09-11 (America/Bogota)

### Added
- **Optimización del lector de noticias (ADR-009)** — se elimina el *cold
  start* de Chromium que hacía lento el primer clic:
  - **Pre-warm del motor**: `NewsReaderView` se instancia oculto a los ~900 ms
    del boot (`QTimer.singleShot`); el primer clic solo navega a la URL real
    del artículo en lugar de arrancar Chrome embebido.
  - **Perfil persistente con caché HTTP en disco** (100 MB) en
    `%APPDATA%\JarvisLauncher\WebEngine`: re-visitas y assets repetidos cargan
    desde caché.
  - **Bloqueo de rastreadores/publicidad** (`_TrackerBlocker`, 17 dominios de
    ads/analytics): menos peticiones y bytes por página; no toca imágenes/CSS
    del sitio.
  - Settings de red: `DnsPrefetchEnabled` habilitado y
    `PlaybackRequiresUserGesture` (sin autoplay de video → menos datos).
  - Fade de apertura del lector reducido de 220 ms a **110 ms** (respuesta
    visual casi instantánea).
  - `JARVIS_DISABLE_WEBENGINE=1`: modo para CI headless que prueba el lector
    completo por el fallback de texto (el renderer de Chromium no navega sin
    GPU).

### Removed
- **`core/feedback.py` y sus 15 llamadas (ADR-010)**: se eliminan los sonidos
  `winsound.Beep` (click/éxito/error) de cards, panel, lector y Ajustes. El
  feedback pasa a ser **100 % visual** (hover, resaltado, sweep, barra de
  estado y notificaciones del sistema); cada clic ya no crea un hilo daemon de
  audio y la UI responde sin ruido.

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

### Lector de noticias (spec v2 puntos 3 y 4)
- `ui/news_reader.py` (`NewsReaderView` + `MiniBrowser` + `MiniNewsItem`):
  **lector de noticias a pantalla completa** que se abre al hacer clic en una
  noticia del panel:
  - **Mini navegador embebido (Chromium)**: `QWebEngineView` carga la **URL
    real del artículo** dentro del launcher, mostrando imágenes, CSS y el
    contenido completo del sitio; botones **⟳** (recargar) y
    **ABRIR ORIGINAL ↗** (navegador externo) en el encabezado
  - **Split-pane redimensionable** (`QSplitter`) con lista compacta a la
    izquierda (título + fuente/hora, artículo actual resaltado) y el mini
    navegador a la derecha
  - **Fallback elegante sin la dependencia**: si `PyQt6-WebEngine` no está
    instalado, el lector muestra el resumen del feed con la tipografía de
    lectura larga de la v2 (lead con capitular, pull-quote en cursiva) en un
    `QTextBrowser`; la app nunca deja de funcionar
  - Navegación por teclado: `←`/`→` cambian de artículo y `Escape` vuelve al
    launcher; feedback de carga en el encabezado ("Cargando artículo…")
- `main.py`: `QApplication.setAttribute(AA_ShareOpenGLContexts, True)` antes
  de crear la app (requisito del WebEngine)
- Panel des saturado: `ui/news_panel.py` elimina el preview apilado (cada
  noticia queda con fuente + hora + título, sin texto encima de otro), altura
  de tarjeta reducida a 88 px, más respiro entre items (spacing 10) y lista
  limitada a 12 noticias; el clic emite `readerRequested(items, index)` y
  abre el lector (el enlace original queda dentro del lector)
- `ui/jarvis_ui.py`: integra `NewsReaderView` bajo demanda
  (`_open_reader` / `_close_reader`), conecta `readerRequested`, prioriza los
  atajos del lector en `keyPressEvent` y aplica el tema vivo al abrir
- `requirements.txt`: añadido `PyQt6-WebEngine>=6.7` como dependencia
  **opcional** (mini navegador del lector; el fallback de texto no la exige).
  Instalada en el entorno: `PyQt6-WebEngine 6.11.0`
- Docs: `docs/ADR-007-lector-noticias.md` actualizado y
  `docs/ADR-008-webengine.md` (decisión del mini navegador: justificación de
  la dependencia y fallback); `docs/Arquitectura.md`, `README.md` y
  `TODO.md` actualizados

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

## [1.3.0] - 2026-09-10 (America/Bogota)

### Added
- Comando global `jarvis`: `assets/jarvis.cmd` + instalador `install_jarvis_cmd.bat`
  que copia el script a `%USERPROFILE%\bin` y lo agrega al PATH de usuario
- Se abre cualquier ventana nueva de CMD o PowerShell y se escribe `jarvis`
  para lanzar el launcher (usa `pythonw.exe`, sin consola y devuelve el prompt)

### Fixed
- El comando resuelve correctamente desde PowerShell y CMD (verificado con
  reconstruccion del PATH desde el registro y lanzamiento real del proceso)

### Docs (histórico absorbido)
- Carpeta `docs/` creada como fuente principal de documentación técnica
  (`Arquitectura.md` + ADR-001/002/003) y enlace desde el README raíz
- README se declara explícitamente como documentación de usuario final

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
