# ADR-006: Siempre al frente, atajo global y bandeja (modo foco v2)

- **Estado**: Aceptado
- **Fecha**: 2026-09-11 (America/Bogota)
- **Versión asociada**: v2.0.0
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode),
  Kuro-chan (frontend)
- **Tipo**: Feature / integración con el sistema operativo

## Contexto

El diseño v2 ("modo foco / workspace") redefine el ciclo de uso del launcher:

1. El launcher debe estar **siempre al frente** mientras el usuario elige un
   modo (nunca quedar detrás de otras ventanas).
2. Al elegir un modo, el launcher debe **ocultarse solo** para dejar al frente
   las aplicaciones lanzadas.
3. Se necesita una forma de **reinvocar el launcher** desde cualquier lugar sin
   depender del comando `jarvis` ni de la consola: atajo global de teclado.
4. El botón **✕** debe **ocultar a la bandeja** (la app sigue viva en segundo
   plano como "asistente"), con salida real solo desde el menú de la bandeja.

Restricciones heredadas: **cero dependencias nuevas** (Python estándar +
PyQt6), ADR-001 (sin `QGraphicsEffect`; efectos pintados a mano) y máxima
compatibilidad con Windows 10/11.

## Opciones consideradas

| Opción | Implementación | Ventajas | Desventajas | Veredicto |
|--------|---------------|----------|-------------|-----------|
| A. `Qt.KeyboardShortcut` + `QShortcut` | Atajo de ventana (necesita foco Qt) | Simple, 100% código Qt | Solo funciona con el launcher enfocado; **no es global** | ❌ No cumple |
| B. `GlobalHotkey` (PySide6) | Librería externa `pynput`/`global-hotkeys` | Atajo global fácil | **Dependencia nueva**; instalación en máquinas limpias | ❌ Violenta las restricciones |
| C. `RegisterHotKey` nativo (ctypes) + `QAbstractNativeEventFilter` | API Windows `RegisterHotKey`/`UnregisterHotKey` con `HWND=0`; filtro de eventos recibe `WM_HOTKEY` y emite señal Qt | Sin dependencias; nativo y estable; señal `activated` en el hilo de la UI; degradación elegante si el atajo está ocupado | Código específico de Windows (`ctypes.windll.user32`) | ✅ Elegida |

Para la **bandeja**, la opción natural es `QSystemTrayIcon` (widget estándar de
Qt, sin dependencias nuevas), con icono generado por código (`QPainter`) para
no depender de assets externos y recolorable según el tema activo.

## Decision

1. **`core/hotkey.py` — `GlobalHotkey`**:
   - Registra `Ctrl+Shift+Espacio` con `RegisterHotKey(hwnd=0, id, 0x0006,
     0x20)` (MOD_CONTROL | MOD_SHIFT, VK_SPACE) vía `ctypes.windll.user32`.
   - Instala un `QAbstractNativeEventFilter`: al recibir `WM_HOTKEY` (0x0312)
     con nuestro id (`0x4A41`), emite la señal `activated` **en el hilo de la
     UI** (seguro para tocar widgets Qt).
   - `unregister()` en el cierre. Si `RegisterHotKey` devuelve 0 (atajo ya en
     uso por otra app), loguea advertencia y **no impide** el resto de la app.
   - Verificado: el registro y el arranque completo pasan en pruebas offscreen;
     la interacción real del mensaje `WM_HOTKEY` se valida en Windows de
     escritorio.
2. **`core/tray.py` — `Tray`**:
   - `QSystemTrayIcon` con icono dibujado por código (anillo HUD + núcleo)
     que se recoloriza con el acento del tema (`set_accent`).
   - Menú contextual: **Mostrar** (`show_and_raise`) y **Salir** (`quit_app`);
     doble clic en el icono también muestra el launcher.
   - `show_message(title, body)` para la notificación de bandeja que indica el
     atajo global al ocultarse.
3. **Comportamiento de ventana (`ui/jarvis_ui.py`)**:
   - `show_and_raise()` = `show()` + `raise_()` + `activateWindow()` en cada
     apertura (arranque, atajo, bandeja).
   - Al elegir modo: `QTimer.singleShot(700, self.hide)` — el retraso permite
     ver el flash de selección y luego deja al frente las apps lanzadas.
   - `closeEvent` con `tray.enabled` = true: `hide()` + `show_message` (la app
     sigue viva); salida real solo con `_force_quit` (menú Salir / cierre del
     SO).
4. **`core/settings.py`**: nueva clave `tray.enabled` (default `true`) con
   migración suave; el panel de control v2 permite desactivar la bandeja.

## Consecuencias

- **Positivas**: el launcher se convierte en un asistente residente invocable
  desde cualquier app; sin dependencias nuevas; los efectos/animaciones siguen
  respetando ADR-001.
- **Negativas / límites**: atajo y bandeja son específicos de **Windows**
  (naturaleza de la app, acotado por diseño); si otro proceso ocupa
  `Ctrl+Shift+Espacio`, el atajo no estará disponible (se loguea advertencia y
  sigue funcionando por bandeja y por `jarvis`); la notificación de bandeja
  depende del soporte nativo del sistema.
- **Pruebas**: offscreen valida registro/arranque sin crash; la validación
  interactiva (foco, `WM_HOTKEY`, clics de bandeja) se hará en la máquina real
  como item del TODO.

## Referencias

- [ADR-001](./ADR-001-quitar-qgraphicseffect.md)
- [ADR-004](./ADR-004-temas-thememanager.md)
- Sección 3 de [Arquitectura.md](./Arquitectura.md): `core/hotkey.py`,
  `core/tray.py`, `ui/jarvis_ui.py`