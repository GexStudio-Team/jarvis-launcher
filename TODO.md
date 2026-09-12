# TODO - J.A.R.V.I.S. Launcher

## Completado

- [x] Estructura base del proyecto
- [x] ConfigManager para leer/write `config.json`
- [x] AppLauncher con lanzamiento en hilo separado
- [x] UI principal con anillos HUD, particulas, scan line, vignette
- [x] Tarjetas de modo animadas (glassmorphism, hover glow)
- [x] Auto-inicio Windows (VBS + boton toggle)
- [x] Deteccion de instancia unica
- [x] Documentacion (README, CHANGELOG, TODO)
- [x] `requirements.txt`
- [x] `.gitignore`
- [x] Repo publico GitHub (GexStudio-Team/jarvis-launcher)
- [x] Fix PyQt6: QDesktopWidget -> QApplication.primaryScreen()
- [x] Fix singleton: retencion global del socket (lock estable)
- [x] Sonidos de feedback (click, exito, error)
- [x] Efecto de typewriter en el greeting
- [x] Pantalla de carga animada al iniciar
- [x] Historial de modos recientes
- [x] Animacion de seleccion con flash de color del modo
- [x] Notificaciones Windows al completar lanzamiento
- [x] soporte multi-monitor
- [x] Fix v1.2.0: eliminar QGraphicsEffect (spam QPainter + cards negras en hover)
- [x] Fix v1.2.0: sonidos con winsound.Beep (ya no dependen del esquema de Windows)
- [x] Fix v1.2.0: resolucion robusta de rutas de apps (PATH, menu inicio, App Paths)
- [x] v1.2.0: beam de energia a la card seleccionada
- [x] v1.2.0: corner brackets HUD en tarjetas + halo de hover manual
- [x] v1.2.0: boot rediseñado con barra de progreso
- [x] v1.3.0: comando global `jarvis` en CMD/PowerShell (install_jarvis_cmd.bat)
- [x] v1.4.0: `core/settings.py` — SettingsManager con `settings.json` (preferencias UI, gitignored)
- [x] v1.4.0: `core/themes.py` — ThemeManager + 8 temas (obsidiana, nocturno, crimson, esmeralda, matriz, violeta, ambar, luz, nieve)
- [x] v1.4.0: `core/news.py` — NewsService RSS/Atom solo stdlib + 10 presets + URL propia
- [x] v1.4.0: `ui/news_panel.py` — panel lateral redimensionable, refresh 10 min, entrada animada, click abre noticia, estado desconectado con CONECTAR
- [x] v1.4.0: `ui/settings_dialog.py` — rueda ⚙ con temas/swatches y ConnectDialog con validacion en hilo (señal Qt)
- [x] v1.4.0: `ui/mode_card.py` — paint 100% custom, icono flotante, zoom hover, sweep, entrada escalonada
- [x] v1.4.0: `ui/jarvis_ui.py` — layout compacto sin huecos, panel noticias lateral izq/der, temas en caliente
- [x] v1.4.0: fix crash `QColor("#hex", n)` (constructores invalidos Qt6) en overwlays/paintEvent
- [x] v1.4.0: fix `ConnectDialog`: reemplazado `QMetaObject.invokeMethod` con kwargs por señal `validationDone`
- [x] v1.4.0: render test offscreen completo (boot, hover, click, panel, 8 temas) 0 errores QPainter
- [x] v1.4.0: prueba en vivo de noticias (18 items reales de 4 fuentes)
- [x] v1.4.0: docs ADR-004 (temas) y ADR-005 (panel noticias); Arquitectura/README/CHANGELOG actualizados
- [x] v1.4.0: release GitHub v1.4.0 publicada (tag v1.4.0, main == origin/main == a6e57a8)
- [x] v2: `core/hotkey.py` — atajo global Ctrl+Shift+Espacio (RegisterHotKey ctypes + QAbstractNativeEventFilter, cero deps)
- [x] v2: `core/tray.py` — bandeja del sistema (icono generado por codigo, menu Mostrar/Salir, doble click)
- [x] v2: `core/greeting.py` — saludo dinamico por franja horaria + adjetivo rotativo por arranque
- [x] v2: `core/github_link.py` — vinculacion real de GitHub (deteccion `gh` autenticado + verificacion API publica, sin secretos)
- [x] v2: `core/settings.py` — claves tray/github/greeting con migracion suave
- [x] v2: `ui/mode_card.py` — cards modo workspace: monograma tipografico en vez de emoji, barra IDE, paleta sobria (modos conservados)
- [x] v2: `ui/news_panel.py` — cabecera "¿Que esta pasando en el mundo ahora?", items con jerarquia limpia (fuente/hora/titulo/preview), estado vacio sin emoji
- [x] v2: `ui/settings_dialog.py` — lista estructurada (1 Apariencia, 2 Comportamiento, 3 Noticias, 4 GitHub, 5 Proximamente) + GithubDialog
- [x] v2: `ui/jarvis_ui.py` — z-order siempra al frente, ocultar al elegir modo, ✕ oculta a bandeja, saludo dinamico, refresh_greeting/toggle_startup publicos
- [x] v2: `main.py` — show_and_raise al arrancar + deteccion automatica de GitHub en hilo
- [x] v2: pruebas offscreen (render UI, tarjetas, noticias, dialogo ajustes, boot completo) 0 errores
- [x] v2: push main -> origin/main (cce3112)
- [x] v2: docs actualizadas — CHANGELOG [2.0.0], README (caracteristicas/atajos/estructura), Arquitectura.md (modulos v2, flujo), ADR-006 (atajo global + bandeja), config.json -> 2.0.0
- [x] v2: `ui/news_reader.py` — NewsReaderView lector fullscreen split-pane (lista izq + lectura larga der, QSplitter) + MiniNewsItem
- [x] v2: tipografia lectura larga — columna centrada, titulo Georgia, lead con capitular, pull-quote cursiva, divisores; HTML del tema activo
- [x] v2: click en noticia del panel emite `readerRequested` y abre el lector; boton "Abrir original" en navegador cuando el feed no trae cuerpo
- [x] v2: atajos del lector (Escape cierra, flechas navegan) priorizados en JarvisUI; fade windowOpacity (ADR-001)
- [x] v2: tests offscreen lector (render, splitter, navegacion, temas, respaldo sin summary) + integracion con JarvisUI 0 errores
- [x] v2: docs ADR-007 (lector), Arquitectura (news_reader + flujo), CHANGELOG [Unreleased], README
- [x] v2: **mini navegador embebido** — `PyQt6-WebEngine` instalado (6.11); `MiniBrowser` con `QWebEngineView` carga la URL real del articulo (imagenes y todo); fallback a QTextBrowser si no esta instalado; `AA_ShareOpenGLContexts` en main
- [x] v2: **panel de noticias des saturado** — sin preview apilado (fuente+hora+titulo), altura 88px, spacing 10, 12 items; lo completo se lee en el lector
- [x] v2: docs ADR-008 (webengine), Arquitectura y README actualizados (requisitos + lector)

## En progreso

- [ ] Merge de `feat/news-reader` a `main` vía PR (propuesta entregada, pendiente de aprobacion y creacion)
- [ ] Release GitHub v2.0.0 + tag (pendiente de la creacion del PR)

## Pendiente

- [ ] Editor grafico de modos (GUI para agregar/quitar apps desde la rueda ⚙)
- [ ] Soporte JSON Feed en noticias
- [ ] Cache offline de items de noticias
- [ ] Filtro de noticias por categoria/idioma
- [ ] Verificar contraste de temas claros en todo el paint custom
- [ ] Editor visual de paletas de temas
- [x] ~~Sonido en hover de tarjetas~~ — **descartado**: feedback 100 % visual
      (ADR-010); reabrir solo si la comunidad pide feedback sonoro
      configurable explícitamente
- [ ] Variar velocidad del typewriter
- [ ] Probar en la maquina real: instalar Discord y Spotify para validar resolucion por nombre
- [ ] Verificacion de toasts de Windows 10/11
- [ ] Prueba de pantalla completa real y posicion en monitores multiples
- [ ] Revisar uso de CPU del core/beam en pantallas grandes

## Validación en máquina real (ADR-009)

- [ ] **Primer clic en noticia**: abrir el lector y confirmar que carga el
      artículo casi al instante (sin el "arranque" de Chromium del clic)
- [ ] Segunda visita al mismo artículo: confirmar salida de caché de disco
      (assets cargan más rápido)
- [ ] Página con rastreadores (p. ej. un portal de noticias): red abierta del
      sistema → comprobar líderes de red menos saturados (los dominios de
      ads/analytics quedan bloqueados)
- [ ] Confirmar que la UI no emite ningún sonido al hacer clic (feedback
      visual únicamente)

---
_Historial de release: v2.0.0 (modo foco + lector), v1.4.0 (temas/noticias/settings),
v1.3.0 (comando global jarvis), v1.2.0 (fix renderizado/sonidos/resolución de apps)._