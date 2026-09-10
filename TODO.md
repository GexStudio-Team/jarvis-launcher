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

## Pendiente

- [ ] Soporte para modo oscuro / claro
- [ ] Editor grafico de modos (GUI para agregar/quitar apps)
- [ ] Scripts predefinidos para mas modos (Docker, Streaming, etc.)
- [ ] Sonido en hover de tarjetas
- [ ] Probar en la maquina real: instalar Discord y Spotify para validar resolucion por nombre
