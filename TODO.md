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

## En progreso

- [ ] Crear release GitHub v1.4.0 (propuesta pendiente de aprobacion)

## Pendiente

- [ ] Editor grafico de modos (GUI para agregar/quitar apps desde la rueda ⚙)
- [ ] Soporte JSON Feed en noticias
- [ ] Cache offline de items de noticias
- [ ] Filtro de noticias por categoria/idioma
- [ ] Verificar contraste de temas claros en todo el paint custom
- [ ] Editor visual de paletas de temas
- [ ] Sonido en hover de tarjetas
- [ ] Variar velocidad del typewriter
- [ ] Probar en la maquina real: instalar Discord y Spotify para validar resolucion por nombre
- [ ] Verificacion de toasts de Windows 10/11
- [ ] Prueba de pantalla completa real y posicion en monitores multiples
- [ ] Revisar uso de CPU del core/beam en pantallas grandes