# J.A.R.V.I.S. Launcher

Interfaz tipo JARVIS (Iron Man) que se ejecuta al iniciar Windows y permite lanzar conjuntos de aplicaciones segun el modo seleccionado: **Gaming**, **Trabajo** o **Estudio**.

## Caracteristicas

- Interfaz fullscreen con efectos HUD: anillos rotantes, particulas flotantes, linea de escaneo
- Pantalla de boot animada tipo arranque de sistema (barra de progreso)
- Greeting con efecto typewriter
- 3 modos predefinidos: Gaming, Trabajo, Estudio (personalizables via `config.json`)
- Animaciones suaves en las tarjetas (hover glow, elevacion, pulse al click)
- Corner brackets estilo HUD y beam de energia hacia la tarjeta seleccionada
- Flash de color del modo al seleccionar
- Sonidos de feedback (click, exito, error) via `winsound.Beep`
- Notificaciones toast de Windows al completar el lanzamiento
- Historial de modos recientes en la barra de estado
- Auto-inicio en Windows (activable/desactivable desde la interfaz)
- Deteccion de instancia unica (no abre dos veces)
- Lanzamiento de apps en hilo separado (no bloquea la UI)
- Soporte multi-monitor (centrado en el monitor primario)
- Resolucion automatica de apps por nombre (PATH, menu inicio, registro App Paths)
- **Panel lateral de noticias RSS**: posicion izquierda/derecha, ancho
  redimensionable arrastrando el borde, actualizacion automatica cada 10
  minutos y clic en una noticia para abrirla en tu navegador
- **Fuentes de noticias**: 10 presets (Google News, BBC Mundo, El Tiempo, El
  Espectador, CNN en Espanol, DW, RT, Hacker News, The Verge, Wired) o pega tu
  propia URL RSS/Atom (se valida antes de conectar)
- **Temas de color**: 8 paletas (obsidiana, nocturno, crimson, esmeralda,
  matriz, violeta, ambar, luz, nieve) selectables desde la rueda de ajustes ⚙

## Requisitos

- Windows 10/11
- Python 3.10+
- PyQt6

## Instalacion

```bash
# 1. Navegar al directorio del proyecto
cd jarvis-launcher

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
python main.py
```

Para detalles de arquitectura, decisiones técnicas (ADRs) y trabajo pendiente
para desarrolladores, consulta [`docs/`](./docs/).

## Comando global `jarvis`

Instala el comando `jarvis` en el PATH de usuario para abrir el launcher
desde **cualquier** CMD o PowerShell:

```bash
install_jarvis_cmd.bat
```

Despues de instalarlo (y abrir una ventana nueva), escribe `jarvis` desde
cualquier directorio:

```powershell
jarvis
```

Para desinstalarlo:

```bash
install_jarvis_cmd.bat --uninstall
```

El comando usa `pythonw.exe` (abre la GUI sin ventana de consola y devuelve
el prompt al instante).

## Configuracion de modos

Edita `config.json` para personalizar los modos y las aplicaciones que se abren en cada uno:

```json
{
    "modes": {
        "gaming": {
            "name": "Gaming",
            "icon": "\U0001f3ae",
            "color": "#FF2D55",
            "description": "Listo para la accion",
            "apps": [
                {
                    "name": "Steam",
                    "command": "C:\\Program Files (x86)\\Steam\\steam.exe"
                },
                {
                    "name": "Discord",
                    "command": "C:\\Users\\TU_USUARIO\\AppData\\Local\\Discord\\Update.exe",
                    "args": "--processStart Discord.exe"
                }
            ]
        }
    }
}
```

### Campos de cada app

| Campo | Tipo | Requerido | Descripcion |
|-------|------|-----------|-------------|
| `name` | string | Si | Nombre que se muestra en el log |
| `command` | string | Si | Ruta al ejecutable, URL o nombre corto de la app |
| `args` | string | No | Argumentos adicionales |

### Resolucion de apps por nombre

Si `command` no es una ruta existente ni una URL, el launcher busca la app
automaticamente en (en orden):

1. Variable de entorno `PATH`
2. Accesos directos del menu de inicio (usuario y sistema)
3. Registro de Windows `App Paths`

Esto permite usar nombres cortos como `"Discord"` o `"Spotify"` sin
depender de rutas fijas que cambian en cada instalacion.

### Como encontrar la ruta de una app

1. Busca el acceso directo en el Menu Inicio
2. Click derecho -> Propiedades
3. Copia el campo "Destino"

## Auto-inicio en Windows

Tienes dos formas:

### Opcion 1: Desde la interfaz
Haz click en el boton **"Configurar auto-inicio"** en la esquina superior derecha.

### Opcion 2: Script manual
Ejecuta como Administrador:
```bash
install_startup.bat
```

Para desactivar, ejecuta el mismo script nuevamente.

## Atajos de teclado

| Tecla | Accion |
|-------|--------|
| `Escape` | Cerrar launcher |
| `F11` | Alternar pantalla completa |

## Noticias y temas (v1.4)

### Rueda de ajustes ⚙

Haz clic en la rueda **⚙** (esquina superior derecha) para abrir el panel de control:

- **Tema**: elige una de las 8 paletas de color (swatches con vista previa).
- **Panel de noticias**: activar/desactivar y elegir posición (izquierda o
  derecha).
- **Fuentes**: botón para abrir el conector de fuentes.

### Conectar una fuente de noticias

1. Abre la rueda ⚙ → **Fuentes**.
2. Elige un preset (Google News, BBC Mundo, El Tiempo, ...) y pulsa **USAR**,
   o pega una **URL RSS/Atom** propia y pulsa **CONECTAR** (se valida que el
   feed sea legible antes de conectar).
3. El panel mostrará las noticias con su antigüedad ("hace 5 min").

### Redimensionar el panel

Arrastra el **borde interior** del panel (cursor ⇔) para cambiar su ancho
(280–560 px). La posición y el ancho se guardan para la próxima sesión.

### Abrir una noticia

Haz clic en cualquier noticia del panel: se abre en tu navegador por defecto.

> Las noticias se actualizan automáticamente cada 10 minutos. Si el panel
> queda "Sin noticias disponibles", verifica tu conexión o cambia de fuente
> desde el conector.

## Estructura del proyecto

```
jarvis-launcher/
├── main.py              # Entry point
├── config.json          # Configuracion de modos (edita aqui)
├── settings.json        # Preferencias de interfaz (tema/noticias, generado automaticamente)
├── state.json           # Estado/historial (generado automaticamente)
├── requirements.txt     # Dependencias Python
├── install_startup.bat  # Instalar/desinstalar auto-inicio
├── install_jarvis_cmd.bat  # Instalar/desinstalar comando global `jarvis`
├── core/
│   ├── config.py        # Gestor de configuracion de modos
│   ├── settings.py      # Preferencias de interfaz (tema, panel de noticias)
│   ├── themes.py        # Paletas y gestor de temas de color
│   ├── news.py          # Servicio de noticias RSS/Atom (stdlib)
│   ├── launcher.py      # Motor de apertura de apps
│   ├── state.py         # Historial de modos recientes
│   ├── feedback.py      # Sonidos de feedback (winsound)
│   └── notifier.py      # Notificaciones toast de Windows
├── ui/
│   ├── jarvis_ui.py     # Ventana principal con efectos HUD
│   ├── mode_card.py     # Tarjetas animadas de modo
│   ├── news_panel.py    # Panel lateral de noticias
│   └── settings_dialog.py  # Rueda de ajustes + conector de fuentes
└── assets/
    ├── startup.vbs      # Script de auto-inicio Windows
    └── jarvis.cmd       # Origen del comando global `jarvis`
└── docs/                # Documentacion tecnica (Arquitectura + ADRs)
```

Nota: `docs/` es la fuente principal de documentación técnica para
desarrolladores; el README está orientado a usuario final.
