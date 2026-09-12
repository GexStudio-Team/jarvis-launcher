# ADR-008: Mini navegador embebido en el lector de noticias (PyQt6-WebEngine)

- **Estado**: Aceptado
- **Fecha**: 2026-09-11 (America/Bogota)
- **Versión asociada**: v2.0.0 (rama `feat/news-reader`)
- **Decisores**: Duvan Altamar (usuario), Technical Partner (opencode),
  Kuro-chan (frontend)
- **Tipo**: Feature / cambio de dependencia

## Contexto

Tras la primera entrega del lector (ADR-007, contenido del feed + "Abrir
original"), el usuario solicitó dos correcciones:

1. **El panel de noticias se ve saturado** ("una cosa encima de la otra"):
   cada tarjeta apilaba fuente + hora + título + preview.
2. **"Quiero que cargue un mini navegador, para que pueda ver imágenes y
   todo"**: la noticia completa se debe evidenciar **desde Jarvis**, no solo el
   resumen del feed ni un salto al navegador externo.

El proyecto arrastra la restricción "cero dependencias nuevas" desde v1.4. Ver
el artículo completo con imágenes y CSS desde el launcher exige un motor de
render web embebido: **tan viable en PyQt6 es `PyQt6-WebEngine`** (Chromium).
Esta decisión la **modifica explícitamente** bajo el visto bueno del usuario.

## Opciones consideradas

| Opción | Implementación | Ventajas | Desventajas | Veredicto |
|--------|---------------|----------|-------------|-----------|
| A. `QWebEngineView` (PyQt6-WebEngine) | Chromium embebido en el widget | Web real: imágenes, CSS, JS, reproducción; integrable al split-pane | Dependencia nueva (~130 MB) y proceso Chromium residente solo al abrir el lector | ✅ Elegida |
| B. `QWebView` (QtWebKit) | WebKit embebido | Ligero | **No existe en PyQt6**; solo PyQt5/PySide2 | ❌ No |
| C. `pywebview` (WebView2/Edge de Windows) | Ventana web del sistema | Nativo, liviano, sin Chromium propio | Otra dependencia; modelo de ventana externa, peor acoplamiento con el split-pane | ❌ Descartada |
| D. `QTextBrowser` + imagen del feed (`media:content`) | Render del resumen + una imagen | Cero deps | **No es la noticia completa**; los feeds solo traen previews cortos | ❌ No cumple el pedido |

## Decision

1. **Agregar `PyQt6-WebEngine>=6.7`** a `requirements.txt` (comentada como
   **opcional**): el fallback garantiza que la app funcione sin ella.
2. **`ui/news_reader.py` — `MiniBrowser(QWidget)`**:
   - `QStackedWidget` con dos páginas: `QWebEngineView` (Chromium) y
     `QTextBrowser` (fallback con el resumen del feed y la tipografía de
     lectura larga v2).
   - `show_article(item, fallback_html)` → carga `item.url` en Chromium si
     está disponible; si no, muestra el HTML de respaldo.
   - **Lazy**: el módulo se importa dentro del constructor (try/except); el
     motor Chromium solo se carga si el usuario abre el lector, no al
     arrancar el launcher.
   - Botones **⟳** (recargar) y **ABRIR ORIGINAL ↗** (navegador externo);
     estado de carga en el encabezado ("Cargando artículo…").
3. **`main.py`**: `QApplication.setAttribute(AA_ShareOpenGLContexts, True)`
   **antes** de crear `QApplication` (requisito del WebEngine).
4. **`ui/news_panel.py` (anti-saturación)**: cada `NewsItemWidget` queda con
   fuente + hora + título únicamente (sin preview apilado), altura 88 px,
   spacing mayor y lista limitada a 12 noticias; el contenido completo vive en
   el lector.

## Consecuencias

- **Positivas**: la noticia se lee completa dentro de Jarvis con imágenes y
  diseño real del sitio; el panel respira (menos información apilada); la UI
  propia sigue sin `QGraphicsEffect` (ADR-001) y con los colores del tema.
- **Negativas**: dependencia nueva y voluminosa (`PyQt6-WebEngine` Chromium);
  por defecto Chromium deja un proceso hijo residente mientras el lector está
  abierto (cerrado al cerrarlo). En entornos sin GPU (offscreen/CI) el
  renderer hace *fallback* a software (warnings esperados).
- **Mitigación**: el fallback de texto es funcional y probado; el requisito en
  `requirements.txt` está marcado como opcional; el lector solo instancia
  Chromium al abrirse.
- **Pruebas**: unitarias (webengine disponible/ausente), render con los 9
  temas, navegación e integración con `JarvisUI` pasan en offscreen; la
  validación visual de la navegación real (`setUrl` → contenido cargado) se
  hace en la máquina de escritorio.

## Referencias

- [ADR-001](./ADR-001-quitar-qgraphicseffect.md)
- [ADR-007](./ADR-007-lector-noticias.md) (lector: split-pane + contenido)
- Sección 3 de [Arquitectura.md](./Arquitectura.md): `ui/news_reader.py`,
  `ui/news_panel.py`, `main.py`
- `requirements.txt`