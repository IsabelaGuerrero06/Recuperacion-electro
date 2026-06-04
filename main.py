"""
Simulador de Interacción Radiación–Materia
Modelo de Lorentz (Oscilador Armónico Forzado)
================================================

Física implementada
-------------------
Campo eléctrico incidente:
    E(x,t) = E0·cos(k·x − ωl·t)

Fuerza sobre el electrón:
    F = q·E

Ecuación del oscilador armónico forzado:
    m·ẍ + k·x = q·E0·cos(ωl·t)

Frecuencia natural de resonancia:
    ωr = √(k/m)

Amplitud de oscilación:
    A_x = q·E0 / (m·(ωr² − ωl²))

Onda incidente:
    f(x,t) = A1·sin(k·x − ωl·t)

Onda emitida por el átomo:
    g(x,t) = A_x·sin(k·x − ωl·t + φ)

Onda resultante (superposición):
    r(x,t) = f(x,t) + g(x,t)

Visualización multicapa (modo incidente_resultante):
    Se distribuyen N átomos equiespaciados.
    Cada segmento [xᵢ, xᵢ₊₁] dibuja:
        r_local(x,t) = f(x,t) + A_x·sin(k·x − ωl·t + φ + k·xᵢ)
    produciendo el desfase acumulado capa a capa.
"""

import sys
import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QFrame,
)
from PyQt6.QtCore import Qt

from ui.wave_canvas import WaveCanvas
from ui.field_canvas import FieldCanvas
from physics.atomo import Atomo
from physics.waves import (
    campo_electrico_incidente,
    campo_electrico_emitido,
    campo_electrico_resultante,
    campo_magnetico_incidente,
    campo_magnetico_emitido,
    campo_magnetico_resultante,
)
from models.sidebar import CalculationSidebar
from models.panel import Panel


# ── Adaptador de campo magnético para escala visual ──────────────

def B_incidente_visual(x, t):
    return campo_magnetico_incidente(x, t) * 3e8


def B_resultante_visual(x, t, atomo):
    return campo_magnetico_resultante(x, t, atomo) * 3e8


def B_emitida_visual(x, t, atomo):
    return campo_magnetico_emitido(x, t, atomo) * 3e8


# ================================================================
# VENTANA PRINCIPAL
# ================================================================

class Simulador(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Simulador Radiación–Materia  |  Modelo de Lorentz  |  N capas"
        )
        self.resize(1400, 800)

        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
            }
        """)

        main_layout = QHBoxLayout(self)

        # ── Átomo de Lorentz ─────────────────────────────────
        hidrogeno = Atomo(
            nombre="Hidrógeno",
            masa=9.1e-31,
            carga=1.6e-19,
            constante_elastica=0.8e-18,
            fase=np.pi / 4
        )

        # ── PANEL IZQUIERDO ──────────────────────────────────

        left_layout = QVBoxLayout()

        simulacion = WaveCanvas(hidrogeno, n_atomos=1)

        self.simulaciones = [simulacion]
        self.is_paused = False

        # ── Controles ────────────────────────────────────────
        controles = Panel()
        controles_layout = QVBoxLayout(controles)
        controles_layout.setContentsMargins(12, 12, 12, 12)
        controles_layout.setSpacing(8)

        self.estado_simulacion = QLabel("Simulación: Activa")
        self.estado_simulacion.setStyleSheet("color: #e0e0e0;")

        self.toggle_btn = QPushButton("Pausar")
        self.toggle_sidebar_btn = QPushButton("Ocultar cálculos")

        self.toggle_btn.clicked.connect(self.toggle_simulacion)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        # ── Control N átomos ─────────────────────────────────
        n_label_row = QHBoxLayout()
        n_label = QLabel("Número de capas (N):")
        n_label.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        self.n_value_label = QLabel("1")
        self.n_value_label.setStyleSheet(
            "color: #ffd166; font-size: 12px; font-weight: bold;"
        )
        n_label_row.addWidget(n_label)
        n_label_row.addStretch()
        n_label_row.addWidget(self.n_value_label)

        self.n_slider = QSlider(Qt.Orientation.Horizontal)
        self.n_slider.setMinimum(1)
        self.n_slider.setMaximum(50)
        self.n_slider.setValue(1)
        self.n_slider.setTickInterval(5)
        self.n_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.n_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffd166;
                border: 1px solid #cc9900;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #ffd16688;
                border-radius: 3px;
            }
        """)
        self.n_slider.valueChanged.connect(self._on_n_changed)

        # Fila de accesos rápidos (N = 1 / 5 / 10 / 20 / 50)
        preset_row = QHBoxLayout()
        preset_row.setSpacing(4)
        for val in [1, 5, 10, 20, 50]:
            btn = QPushButton(str(val))
            btn.setFixedWidth(38)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2a2a2a;
                    color: #aaaaaa;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 2px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background: #3a3a3a;
                    color: #ffd166;
                    border-color: #ffd166;
                }
            """)
            btn.clicked.connect(lambda checked, v=val: self._set_n(v))
            preset_row.addWidget(btn)
        preset_row.addStretch()

        # ── Control phase_kick ────────────────────────────────
        # Contenedor para phase_kick (se ocultará cuando no esté en modo phase_kick)
        self.pk_container = QWidget()
        pk_container_layout = QVBoxLayout(self.pk_container)
        pk_container_layout.setContentsMargins(0, 0, 0, 0)
        pk_container_layout.setSpacing(6)

        pk_label_row = QHBoxLayout()
        pk_label = QLabel("Phase kick por capa:")
        pk_label.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        self.pk_value_label = QLabel("0.80 rad")
        self.pk_value_label.setStyleSheet(
            "color: #ff6666; font-size: 12px; font-weight: bold;"
        )
        pk_label_row.addWidget(pk_label)
        pk_label_row.addStretch()
        pk_label_row.addWidget(self.pk_value_label)

        # Slider de 0 a 3.14 rad, resolución 0.01 → int * 0.01
        self.pk_slider = QSlider(Qt.Orientation.Horizontal)
        self.pk_slider.setMinimum(0)
        self.pk_slider.setMaximum(314)   # 0.00 … 3.14 rad
        self.pk_slider.setValue(80)      # 0.80 rad por defecto
        self.pk_slider.setTickInterval(31)
        self.pk_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pk_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff6666;
                border: 1px solid #cc2222;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #ff666688;
                border-radius: 3px;
            }
        """)
        self.pk_slider.valueChanged.connect(self._on_pk_changed)

        pk_container_layout.addLayout(pk_label_row)
        pk_container_layout.addWidget(self.pk_slider)
        
        # Por defecto, ocultado (solo se muestra en modo phase_kick)
        self.pk_container.setVisible(False)

        controles_layout.addWidget(self.estado_simulacion)
        controles_layout.addWidget(self.toggle_btn)
        controles_layout.addWidget(self.toggle_sidebar_btn)
        controles_layout.addLayout(n_label_row)
        controles_layout.addWidget(self.n_slider)
        controles_layout.addLayout(preset_row)
        controles_layout.addWidget(self.pk_container)
        controles_layout.addStretch(1)

        left_layout.addWidget(simulacion, 7)
        left_layout.addWidget(controles, 3)

        # ── PANEL DERECHO ─────────────────────────────────────

        right_layout = QVBoxLayout()

        campo_electrico = FieldCanvas(
            atomo=hidrogeno,
            incidente_func=campo_electrico_incidente,
            resultante_func=campo_electrico_resultante,
            emitida_func=campo_electrico_emitido,
            color="#00bfff",
            titulo="Campo Eléctrico  E(x,t)"
        )

        campo_magnetico = FieldCanvas(
            atomo=hidrogeno,
            incidente_func=B_incidente_visual,
            resultante_func=B_resultante_visual,
            emitida_func=B_emitida_visual,
            color="#ff4477",
            titulo="Campo Magnético  B(x,t)"
        )

        self.sidebar = CalculationSidebar(
            simulacion,
            hidrogeno,
            on_wave_mode_change=self.set_wave_mode,
        )

        self.simulaciones += [
            campo_electrico,
            campo_magnetico,
            self.sidebar,
        ]

        self.wave_targets = [
            simulacion,
            campo_electrico,
            campo_magnetico,
        ]

        # Guardar referencia al canvas principal para el slider N
        self.simulacion_principal = simulacion

        right_layout.addWidget(campo_electrico, 3)
        right_layout.addWidget(campo_magnetico, 3)
        right_layout.addWidget(self.sidebar,    4)

        # ── DISTRIBUCIÓN GENERAL ──────────────────────────────

        main_layout.addLayout(left_layout,  7)
        main_layout.addLayout(right_layout, 3)

    # ── Control N átomos ─────────────────────────────────────

    def _on_n_changed(self, value):
        self.n_value_label.setText(str(value))
        self.simulacion_principal.set_n_atomos(value)

    def _set_n(self, value):
        self.n_slider.setValue(value)

    def _on_pk_changed(self, value):
        rad = value / 100.0
        self.pk_value_label.setText(f"{rad:.2f} rad")
        self.simulacion_principal.set_phase_kick(rad)

    # ── Control de simulación ─────────────────────────────────

    def toggle_simulacion(self):
        if self.is_paused:
            for s in self.simulaciones:
                s.start()
            self.estado_simulacion.setText("Simulación: Activa")
            self.toggle_btn.setText("Pausar")
            self.is_paused = False
        else:
            for s in self.simulaciones:
                s.pause()
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
        # Mostrar/ocultar slider de phase_kick según el modo
        self.pk_container.setVisible(mode == "phase_kick")


# ================================================================
# PUNTO DE ENTRADA
# ================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Simulador()
    ventana.show()
    sys.exit(app.exec())