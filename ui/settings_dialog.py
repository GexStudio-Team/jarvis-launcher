"""
ui/settings_dialog.py - Dialogo de ajustes del Jarvis Launcher (rueda).

Opciones que expone:
  - Tema de color (obsidiana, nocturno, crimson, esmeralda, matriz,
    violeta, ambar, luz, nieve).
  - Panel de noticias: habilitar/deshabilitar, posicion (izq/der).
  - Fuentes RSS: elegir entre presets, pegar URL propia, conectar/desconectar.

La conexion de fuentes abre un subdialogo (ConnectDialog) que muestra los
presets y permite una URL RSS/Atom personalizada (validada).
"""

from __future__ import annotations

import threading

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QLineEdit,
    QMessageBox,
    QFrame,
    QRadioButton,
)

from core.feedback import play_click
from core.news import NewsService, PRESET_SOURCES
from core.themes import ThemeManager

# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------


def _mk_title(text: str, accent: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont("Segoe UI", 10, QFont.Weight.Bold)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
    lbl.setFont(f)
    lbl.setStyleSheet(f"background: transparent; color: {accent};")
    return lbl


def _mk_btn(text: str, accent: str, bg_soft: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background: {bg_soft};
            color: {accent};
            border: 1px solid {accent};
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background: {accent};
            color: {bg_soft};
        }}
        """
    )
    return btn


class ThemeSwatch(QPushButton):
    """Boton de seleccion de tema con vista previa de color."""

    def __init__(self, theme, current: bool, parent=None) -> None:
        super().__init__(parent)
        self.theme_id = theme.id
        self.theme_name = theme.name
        self.accent = theme.accent
        self.bg = theme.bg
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(72, 56)
        self.setCheckable(True)
        self.setChecked(current)
        self.setToolTip(theme.name)
        self._paint()

    def _paint(self) -> None:
        accent = self.accent
        bg = self.bg
        checked = "1px solid " + accent
        border = "2px solid " + accent if self.isChecked() else f"1px solid {accent}55"
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {bg};
                border: {border};
                border-radius: 8px;
            }}
            QPushButton:hover {{ border: 2px solid {accent}; }}
            """
        )

    def paintEvent(self, event) -> None:
        # Dibuja una mini-vista previa (barra de acento + fondo)
        super().paintEvent(event)
        from PyQt6.QtGui import QPainter, QBrush, QPen

        p = QPainter(self)
        w, h = self.width(), self.height()
        # Acento como barra inferior
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.accent))
        p.drawRect(4, h - 10, w - 8, 6)

    def update_checked(self, checked: bool) -> None:
        self.setChecked(checked)
        self._paint()


# ----------------------------------------------------------------------
# Dialogo de conexion de fuentes (modal para presets + URL personal)
# ----------------------------------------------------------------------


class ConnectDialog(QDialog):
    """
    Modal para elegir fuentes de noticias.

    - Lista de fuentes predefinidas (presets).
    - Campo para pegar una URL RSS/Atom personalizada (con validacion).
    - Conectado -> actualiza SettingsManager y cierra con True.
    """

    # Resultado de la validacion de URL (emitida desde el hilo de trabajo)
    validationDone = pyqtSignal(bool, str)

    def __init__(
        self,
        settings,
        theme: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self._service = NewsService()
        self.validationDone.connect(self._validated)
        self.setWindowTitle("Conectar fuente de noticias")
        self.setModal(True)
        self.setMinimumSize(520, 440)
        self._build()
        self._apply_theme()

    def _build(self) -> None:
        them = self._theme.theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 16)
        outer.setSpacing(12)

        title = _mk_title("CONECTAR FUENTE DE NOTICIAS", them.accent)
        outer.addWidget(title)

        subtitle = QLabel(
            "Elige una fuente predefinida o pega el enlace RSS/Atom de tu app favorita.",
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 11px;"
        )
        outer.addWidget(subtitle)

        # --- Presets en scroll ---
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        preset_container = QWidget()
        preset_layout = QVBoxLayout(preset_container)
        preset_layout.setContentsMargins(0, 0, 8, 0)
        preset_layout.setSpacing(6)

        for src in PRESET_SOURCES:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            row_layout.setSpacing(8)

            name_lbl = QLabel(src["name"])
            name_lbl.setStyleSheet(
                f"background: transparent; color: {them.text}; font-size: 12px;"
            )
            url_lbl = QLabel(src["url"])
            url_lbl.setStyleSheet(
                f"background: transparent; color: {them.text_dim}; font-size: 9px;"
            )
            url_lbl.setWordWrap(True)

            row_layout.addWidget(name_lbl, 1)
            url_col = QVBoxLayout()
            url_col.addWidget(url_lbl)
            row_layout.addLayout(url_col, 2)

            btn = _mk_btn("USAR", them.accent, them.accent_soft)
            btn.setFixedSize(64, 28)
            btn.clicked.connect(
                lambda _=False, n=src["name"], u=src["url"]: self._connect(n, u)
            )
            row_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

            preset_layout.addWidget(row)

        preset_layout.addStretch()
        scroll.setWidget(preset_container)
        outer.addWidget(scroll, 1)

        # --- URL personalizada ---
        custom_row = QHBoxLayout()
        custom_row.setSpacing(8)
        self._url_edit = QLineEdit(self)
        self._url_edit.setPlaceholderText("https://ejemplo.com/feed.xml")
        self._url_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background: {them.bg};
                color: {them.text};
                border: 1px solid {them.card_border};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {them.accent}; }}
            """
        )
        custom_row.addWidget(self._url_edit, 1)

        connect_btn = _mk_btn("CONECTAR", them.accent, them.accent_soft)
        connect_btn.clicked.connect(self._connect_custom)
        custom_row.addWidget(connect_btn)

        outer.addLayout(custom_row)
        self._connect_btn = connect_btn
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"background: transparent; color: {them.accent}; font-size: 10px;"
        )
        outer.addWidget(self._status)

        # Cerrar
        close_row = QHBoxLayout()
        close_row.addStretch()
        cancel_btn = _mk_btn("CERRAR", them.text_dim, them.bg_alt)
        cancel_btn.clicked.connect(self.reject)
        close_row.addWidget(cancel_btn)
        outer.addLayout(close_row)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"QDialog {{ background: {self._theme.theme.bg}; color: {self._theme.theme.text}; }}"
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _connect(self, name: str, url: str) -> None:
        play_click()
        self._settings.news_sources = [{"name": name, "url": url}]
        self._settings.news_enabled = True
        self._status.setText(f"Conectado a {name}")
        QMessageBox.information(
            self, "Conectado", f"Fuente conectada: {name}\nLas noticias se actualizaran automaticamente."
        )
        self.accept()

    def _connect_custom(self) -> None:
        url = self._url_edit.text().strip()
        if not url:
            self._status.setText("Escribe una URL RSS/Atom primero.")
            return

        play_click()
        self._connect_btn.setEnabled(False)
        self._connect_btn.setText("VERIFICANDO...")
        self._status.setText("Comprobando enlace...")

        def _work() -> None:
            ok = self._service.validate_url(url)
            # Resultado al hilo principal (entrega segura via senal)
            self.validationDone.emit(ok, url)

        threading.Thread(target=_work, daemon=True).start()

    def _validated(self, __ok: bool = False, __url: str = "") -> None:
        self._connect_btn.setEnabled(True)
        self._connect_btn.setText("CONECTAR")
        if __ok:
            self._connect("Feed personalizado", __url)
        else:
            self._status.setText(
                "No se pudo leer el feed. Verifica el enlace (debe ser RSS/Atom)."
            )


# ----------------------------------------------------------------------
# Dialogo principal de ajustes (rueda)
# ----------------------------------------------------------------------


class SettingsDialog(QDialog):
    """Panel de control del launcher: temas + configuracion del panel."""

    def __init__(self, settings, theme: ThemeManager, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme = theme
        self.setWindowTitle("Panel de control")
        self.setModal(True)
        self.setMinimumSize(560, 520)
        self._build()
        self._apply_theme()

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------

    def _build(self) -> None:
        them = self._theme.theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 18)
        outer.setSpacing(14)

        title = _mk_title("PANEL DE CONTROL", them.accent)
        outer.addWidget(title)

        # ----- 1. TEMA -----
        section_tema = _mk_title("1 · Apariencia (tema de color)", them.accent)
        outer.addWidget(section_tema)

        theme_scroll = QScrollArea(self)
        theme_scroll.setWidgetResizable(True)
        theme_scroll.setFrameShape(QFrame.Shape.NoFrame)
        theme_scroll.setFixedHeight(96)
        theme_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        theme_container = QWidget()
        theme_layout = QHBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(10)

        self._swatches: dict[str, ThemeSwatch] = {}
        for t in ThemeManager.available_themes():
            swatch = ThemeSwatch(t, current=(t.id == self._theme.theme_id))
            swatch.clicked.connect(lambda _=False, tid=t.id: self._on_theme_selected(tid))
            self._swatches[t.id] = swatch
            theme_layout.addWidget(swatch)
        theme_layout.addStretch()

        theme_scroll.setWidget(theme_container)
        outer.addWidget(theme_scroll)
        self._theme_row = theme_layout

        # ----- 2. PANEL DE NOTICIAS -----
        section_news = _mk_title("2 · Panel de noticias", them.accent)
        outer.addWidget(section_news)

        # Habilitar
        self._enable_radio = QRadioButton("Activar panel de noticias")
        self._disable_radio = QRadioButton("Desactivar panel")
        self._enable_radio.setChecked(self._settings.news_enabled)
        self._disable_radio.setChecked(not self._settings.news_enabled)
        for rb in (self._enable_radio, self._disable_radio):
            rb.setStyleSheet(
                f"background: transparent; color: {them.text}; font-size: 12px;"
            )
        enable_row = QHBoxLayout()
        enable_row.addWidget(self._enable_radio)
        enable_row.addWidget(self._disable_radio)
        enable_row.addStretch()
        outer.addLayout(enable_row)

        # Posicion
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Posición:"))
        self._pos_left = QRadioButton("Izquierda")
        self._pos_right = QRadioButton("Derecha")
        self._pos_left.setChecked(self._settings.news_position == "left")
        self._pos_right.setChecked(self._settings.news_position == "right")
        for pos in (self._pos_left, self._pos_right):
            pos.setStyleSheet(
                f"background: transparent; color: {them.text}; font-size: 12px;"
            )
        pos_row.addWidget(self._pos_left)
        pos_row.addWidget(self._pos_right)
        pos_row.addStretch()
        outer.addLayout(pos_row)

        # Fuentes
        sources_label = QLabel("Fuente conectada:")
        sources_label.setStyleSheet(
            f"background: transparent; color: {them.text_dim}; font-size: 11px;"
        )
        outer.addWidget(sources_label)

        sources_row = QHBoxLayout()
        current = self._current_sources_text()
        self._sources_lbl = QLabel(current)
        self._sources_lbl.setWordWrap(True)
        self._sources_lbl.setStyleSheet(
            f"background: transparent; color: {them.text}; font-size: 11px;"
        )
        sources_row.addWidget(self._sources_lbl, 1)

        self._connect_btn = _mk_btn("CONECTAR / CAMBIAR", them.accent, them.accent_soft)
        self._connect_btn.clicked.connect(self._open_connect_dialog)
        sources_row.addWidget(self._connect_btn, alignment=Qt.AlignmentFlag.AlignRight)
        outer.addLayout(sources_row)

        # ----- 3. ACCIONES -----
        action_row = QHBoxLayout()
        action_row.addStretch()

        self._cancel_btn = _mk_btn("CANCELAR", them.text_dim, them.bg_alt)
        self._cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(self._cancel_btn)

        self._apply_btn = _mk_btn("APLICAR", them.accent, them.accent_soft)
        self._apply_btn.clicked.connect(self._apply_and_close)
        action_row.addWidget(self._apply_btn)
        outer.addLayout(action_row)

    def _current_sources_text(self) -> str:
        srcs = self._settings.news_sources
        if not srcs:
            return "Sin conexión. Pulsa CONECTAR para elegir una fuente."
        return " • ".join(s.get("name", s.get("url", "?")) for s in srcs)

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def _on_theme_selected(self, theme_id: str) -> None:
        play_click()
        self._theme.set_theme(theme_id)
        self._apply_theme()
        for tid, swatch in self._swatches.items():
            swatch.update_checked(tid == theme_id)

    # ------------------------------------------------------------------
    # Noticias / conexion
    # ------------------------------------------------------------------

    def _open_connect_dialog(self) -> None:
        dlg = ConnectDialog(self._settings, self._theme, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._sources_lbl.setText(self._current_sources_text())
            self._enable_radio.setChecked(True)
            # Refrescar panel en vivo
            parent_ui = self.parent()
            if parent_ui is not None and hasattr(parent_ui, "refresh_news"):
                parent_ui.refresh_news()

    # ------------------------------------------------------------------
    # Aplicar
    # ------------------------------------------------------------------

    def _apply_and_close(self) -> None:
        play_click()
        # Tema
        self._settings.theme = self._theme.theme_id
        # Noticias
        enabled = self._enable_radio.isChecked()
        self._settings.news_enabled = enabled
        if self._pos_left.isChecked():
            self._settings.news_position = "left"
        else:
            self._settings.news_position = "right"
        # Aplicar en la UI padre
        parent_ui = self.parent()
        if parent_ui is not None:
            if hasattr(parent_ui, "apply_theme"):
                parent_ui.apply_theme()
            if hasattr(parent_ui, "apply_news_panel"):
                parent_ui.apply_news_panel()
        self.accept()

    # ------------------------------------------------------------------
    # Theme painting
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        them = self._theme.theme
        self.setStyleSheet(f"QDialog {{ background: {them.bg}; color: {them.text}; }}")
        for swatch in self._swatches.values():
            swatch._paint()
        self._sources_lbl.setStyleSheet(
            f"background: transparent; color: {them.text}; font-size: 11px;"
        )