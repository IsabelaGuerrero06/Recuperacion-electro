"""
Simulador de Interacción Radiación-Materia
Modelo de Lorentz (Oscilador Armónico Forzado)
"""

import sys
import numpy as np

from PyQt6.QtWidgets import ( 
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QFrame,
)
from PyQt6.QtCore import Qt

from ui.wave_canvas import WaveCanvas
from ui.field_canvas import FieldCanvas
from models.reloj import RelojGlobal
from physics.atomo import Atomo
from physics.waves import (
    campo_electrico_incidente, campo_electrico_emitido, campo_electrico_resultante,
    campo_magnetico_incidente, campo_magnetico_emitido, campo_magnetico_resultante,
    OMEGA_L,
)
from models.sidebar import CalculationSidebar
from models.panel import Panel


# ── k de resonancia ──────────────────────────────────────────────
# k_res = m · ωl²  →  ωr = ωl cuando k = k_res
M_ELECTRON = 9.1e-31
K_RESONANCIA = M_ELECTRON * OMEGA_L**2   # ≈ 0.1293 N/m


# ── Adaptadores campo magnético ───────────────────────────────────
def B_incidente_visual(x, t):
    return campo_magnetico_incidente(x, t) * 3e8

def B_resultante_visual(x, t, atomo):
    return campo_magnetico_resultante(x, t, atomo) * 3e8

def B_emitida_visual(x, t, atomo):
    return campo_magnetico_emitido(x, t, atomo) * 3e8


# ── Estilo compartido para sliders ────────────────────────────────
def _slider_style(color_handle, color_sub):
    return f"""
        QSlider::groove:horizontal {{
            background: #333; height: 6px; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {color_handle};
            border: 1px solid {color_sub};
            width: 14px; height: 14px; margin: -4px 0; border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{
            background: {color_sub}88; border-radius: 3px;
        }}
    """


# ================================================================
# VENTANA PRINCIPAL
# ================================================================

class Simulador(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador Radiación–Materia  |  Modelo de Lorentz  |  N capas")
        self.resize(1400, 800)
        self.setStyleSheet("QWidget { background-color: #121212; }")

        main_layout = QHBoxLayout(self)

        # ── Átomo ────────────────────────────────────────────
        # Arrancamos con k = 10% de k_resonancia para que la
        # amplitud emitida sea visible desde el inicio.
        k_inicial = 0.10 * K_RESONANCIA
        hidrogeno = Atomo(
            nombre="Hidrógeno",
            masa=M_ELECTRON,
            carga=1.6e-19,
            constante_elastica=k_inicial,
        )

        # ── PANEL IZQUIERDO ──────────────────────────────────
        left_layout = QVBoxLayout()
        # ── Reloj global compartido ───────────────────────────
        self.reloj = RelojGlobal(dt=1e-18, time_scale=200.0, fps=16)

        simulacion = WaveCanvas(hidrogeno, reloj=self.reloj, n_atomos=1)
        self.simulaciones = [simulacion]
        self.is_paused = False

        controles = Panel()
        cl = QVBoxLayout(controles)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(8)

        self.estado_simulacion = QLabel("Simulación: Activa")
        self.estado_simulacion.setStyleSheet("color: #e0e0e0;")
        self.toggle_btn = QPushButton("Pausar")
        self.toggle_sidebar_btn = QPushButton("Ocultar cálculos")
        self.toggle_btn.clicked.connect(self.toggle_simulacion)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        # ── Slider N átomos ───────────────────────────────────
        n_row = QHBoxLayout()
        n_label = QLabel("Número de capas (N):")
        n_label.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        self.n_value_label = QLabel("1")
        self.n_value_label.setStyleSheet("color: #ffd166; font-size: 12px; font-weight: bold;")
        n_row.addWidget(n_label); n_row.addStretch(); n_row.addWidget(self.n_value_label)

        self.n_slider = QSlider(Qt.Orientation.Horizontal)
        self.n_slider.setMinimum(1); self.n_slider.setMaximum(256)
        self.n_slider.setValue(1)
        self.n_slider.setTickInterval(25)
        self.n_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.n_slider.setStyleSheet(_slider_style("#ffd166", "#cc9900"))
        self.n_slider.valueChanged.connect(self._on_n_changed)

        preset_row = QHBoxLayout(); preset_row.setSpacing(4)
        for val in [1, 10, 50, 100, 256]:
            btn = QPushButton(str(val)); btn.setFixedWidth(38)
            btn.setStyleSheet("""
                QPushButton { background:#2a2a2a; color:#aaaaaa; border:1px solid #555;
                              border-radius:4px; padding:2px; font-size:10px; }
                QPushButton:hover { background:#3a3a3a; color:#ffd166; border-color:#ffd166; }
            """)
            btn.clicked.connect(lambda checked, v=val: self._set_n(v))
            preset_row.addWidget(btn)
        preset_row.addStretch()

        # ── Slider K (constante elástica) ─────────────────────
        # Rango: 1 % … 300 % de k_resonancia (paso 1 %)
        # En resonancia (100 %) → ωr = ωl → amplitud máxima / inversión de fase
        k_row = QHBoxLayout()
        k_label = QLabel("Constante K  (% de k_res):")
        k_label.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        self.k_value_label = QLabel("10 %  (sub-res)")
        self.k_value_label.setStyleSheet("color: #66ff66; font-size: 11px; font-weight: bold;")
        k_row.addWidget(k_label); k_row.addStretch(); k_row.addWidget(self.k_value_label)

        self.k_slider = QSlider(Qt.Orientation.Horizontal)
        self.k_slider.setMinimum(1)     # 1 % de k_res
        self.k_slider.setMaximum(300)   # 300 % de k_res
        self.k_slider.setValue(10)      # 10 % — visible y sub-resonante
        self.k_slider.setTickInterval(25)
        self.k_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.k_slider.setStyleSheet(_slider_style("#66ff66", "#33cc33"))
        self.k_slider.valueChanged.connect(self._on_k_changed)

        # Presets de K: sub-res / resonancia / super-res
        k_preset_row = QHBoxLayout(); k_preset_row.setSpacing(4)
        for pct, label in [(10, "10%"), (50, "50%"), (99, "~res"), (150, "150%"), (300, "300%")]:
            btn = QPushButton(label); btn.setFixedWidth(42)
            btn.setStyleSheet("""
                QPushButton { background:#2a2a2a; color:#aaaaaa; border:1px solid #555;
                              border-radius:4px; padding:2px; font-size:10px; }
                QPushButton:hover { background:#3a3a3a; color:#66ff66; border-color:#66ff66; }
            """)
            btn.clicked.connect(lambda checked, v=pct: self.k_slider.setValue(v))
            k_preset_row.addWidget(btn)
        k_preset_row.addStretch()

        # ── Phase kick (visible solo en modo phase_kick) ───────
        self.pk_container = QWidget()
        pk_cl = QVBoxLayout(self.pk_container)
        pk_cl.setContentsMargins(0, 0, 0, 0); pk_cl.setSpacing(6)

        pk_row = QHBoxLayout()
        pk_label = QLabel("Phase kick por capa:")
        pk_label.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        self.pk_value_label = QLabel("0.00 rad")
        self.pk_value_label.setStyleSheet("color: #ff6666; font-size: 12px; font-weight: bold;")
        pk_row.addWidget(pk_label); pk_row.addStretch(); pk_row.addWidget(self.pk_value_label)

        self.pk_slider = QSlider(Qt.Orientation.Horizontal)
        self.pk_slider.setMinimum(0); self.pk_slider.setMaximum(70)
        self.pk_slider.setValue(0)
        self.pk_slider.setTickInterval(31)
        self.pk_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pk_slider.setStyleSheet(_slider_style("#ff6666", "#cc2222"))
        self.pk_slider.valueChanged.connect(self._on_pk_changed)

        pk_cl.addLayout(pk_row)
        pk_cl.addWidget(self.pk_slider)
        self.pk_container.setVisible(False)

        # ── Ensamblar controles ───────────────────────────────
        cl.addWidget(self.estado_simulacion)
        cl.addWidget(self.toggle_btn)
        cl.addWidget(self.toggle_sidebar_btn)
        cl.addLayout(n_row)
        cl.addWidget(self.n_slider)
        cl.addLayout(preset_row)
        cl.addLayout(k_row)
        cl.addWidget(self.k_slider)
        cl.addLayout(k_preset_row)
        cl.addWidget(self.pk_container)
        cl.addStretch(1)

        left_layout.addWidget(simulacion, 7)
        left_layout.addWidget(controles, 3)

        # ── PANEL DERECHO ─────────────────────────────────────
        right_layout = QVBoxLayout()

        campo_electrico = FieldCanvas(
            atomo=hidrogeno,
            reloj=self.reloj,
            incidente_func=campo_electrico_incidente,
            resultante_func=campo_electrico_resultante,
            emitida_func=campo_electrico_emitido,
            color="#00bfff",
            titulo="Campo Eléctrico  E(x,t)",
        )
        campo_magnetico = FieldCanvas(
            atomo=hidrogeno,
            reloj=self.reloj,
            incidente_func=B_incidente_visual,
            resultante_func=B_resultante_visual,
            emitida_func=B_emitida_visual,
            color="#ff4477",
            titulo="Campo Magnético  B(x,t)",
        )

        self.sidebar = CalculationSidebar(
            simulacion, hidrogeno,
            on_wave_mode_change=self.set_wave_mode,
        )

        self.simulaciones += [campo_electrico, campo_magnetico, self.sidebar]
        self.wave_targets  = [simulacion, campo_electrico, campo_magnetico]
        self.simulacion_principal = simulacion

        right_layout.addWidget(campo_electrico, 3)
        right_layout.addWidget(campo_magnetico, 3)
        right_layout.addWidget(self.sidebar,    4)

        main_layout.addLayout(left_layout,  7)
        main_layout.addLayout(right_layout, 3)

    # ── Handlers ─────────────────────────────────────────────

    def _on_n_changed(self, value):
        self.n_value_label.setText(str(value))
        self.simulacion_principal.set_n_atomos(value)
        self.sidebar.set_n_atomos(value)

    def _set_n(self, value):
        self.n_slider.setValue(value)

    def _on_k_changed(self, pct):
        """
        pct = 1..300  →  k = pct/100 × k_resonancia

        Etiqueta indica si estamos sub-resonante, en resonancia o super-resonante.
        Evitamos pct == 100 exacto (división por cero); el slider salta de 99 a 101.
        """
        if pct == 100:
            # Exactamente en resonancia → denominador cero, saltar
            self.k_slider.setValue(101)
            return

        k_valor = (pct / 100.0) * K_RESONANCIA
        if pct < 100:
            zona = "sub-res"
        elif pct > 100:
            zona = "super-res"
        else:
            zona = "resonancia"
        self.k_value_label.setText(f"{pct} %  ({zona})")

        # Actualizar átomo en todos los componentes
        for target in self.wave_targets:
            target.atomo.set_k(k_valor)
            target.update()
        self.sidebar.atomo.set_k(k_valor)
        self.sidebar.update_values()

    def _on_pk_changed(self, value):
        rad = value / 100.0
        self.pk_value_label.setText(f"{rad:.2f} rad")
        self.simulacion_principal.set_phase_kick(rad)

    def toggle_simulacion(self):
        if self.is_paused:
            self.reloj.start()
            self.sidebar.start()
            self.estado_simulacion.setText("Simulación: Activa")
            self.toggle_btn.setText("Pausar")
            self.is_paused = False
        else:
            self.reloj.pause()
            self.sidebar.pause()
            self.estado_simulacion.setText("Simulación: Pausada")
            self.toggle_btn.setText("Reanudar")
            self.is_paused = True

    def toggle_sidebar(self):
        visible = self.sidebar.isVisible()
        self.sidebar.setVisible(not visible)
        self.toggle_sidebar_btn.setText(
            "Mostrar cálculos" if visible else "Ocultar cálculos"
        )

    def set_wave_mode(self, mode):
        for target in self.wave_targets:
            target.set_wave_mode(mode)
        self.pk_container.setVisible(mode == "phase_kick")


# ================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Simulador()
    ventana.show()
    sys.exit(app.exec())