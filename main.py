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

Campo eléctrico resultante:
    E_res = E_inc + E_emit

Campo magnético (onda plana en vacío: B = E/c):
    B_inc  = (E0/c)·cos(k·x − ωl·t)
    B_emit = (A_x/c)·cos(k·x − ωl·t + φ)
    B_res  = B_inc + B_emit
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
)

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
# B es ~1e-8 T (muy pequeño). Multiplicamos por c para que sea
# visible en el canvas (misma escala que E, en unidades visuales).

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
            "Simulador Radiación–Materia  |  Modelo de Lorentz"
        )
        self.resize(1400, 800)

        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
            }
        """)

        main_layout = QHBoxLayout(self)

        # ── Átomo de Lorentz ─────────────────────────────────
        #
        # Parámetros elegidos para que ωl ≠ ωr (sin resonancia)
        # y A_x sea visible en pantalla.
        #
        # ωl = 2π·c/λ_visual = 2π·(3e8)/(5e-6) ≈ 3.77e14 rad/s
        # ωr = √(k/m) = √(0.8e-18 / 9.1e-31) ≈ 2.96e6 rad/s
        #
        # Nota: en el simulador λ_visual = λ_1 × 10 para visualización.

        hidrogeno = Atomo(
            nombre="Hidrógeno",
            masa=9.1e-31,            # masa del electrón (kg)
            carga=1.6e-19,           # carga del electrón (C)
            constante_elastica=0.8e-18,  # N/m  (ligadura)
            fase=np.pi / 4           # desfase φ (rad)
        )

        # ── PANEL IZQUIERDO ──────────────────────────────────

        left_layout = QVBoxLayout()

        simulacion = WaveCanvas(hidrogeno)

        self.simulaciones = [simulacion]
        self.is_paused = False

        # Controles
        controles = Panel()
        controles_layout = QVBoxLayout(controles)
        controles_layout.setContentsMargins(12, 12, 12, 12)
        controles_layout.setSpacing(10)

        self.estado_simulacion = QLabel("Simulación: Activa")
        self.estado_simulacion.setStyleSheet("color: #e0e0e0;")

        self.toggle_btn = QPushButton("Pausar")
        self.toggle_sidebar_btn = QPushButton("Ocultar cálculos")

        self.toggle_btn.clicked.connect(self.toggle_simulacion)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)

        controles_layout.addWidget(self.estado_simulacion)
        controles_layout.addWidget(self.toggle_btn)
        controles_layout.addWidget(self.toggle_sidebar_btn)
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

        right_layout.addWidget(campo_electrico, 3)
        right_layout.addWidget(campo_magnetico, 3)
        right_layout.addWidget(self.sidebar,    4)

        # ── DISTRIBUCIÓN GENERAL ──────────────────────────────

        main_layout.addLayout(left_layout,  7)
        main_layout.addLayout(right_layout, 3)

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


# ================================================================
# PUNTO DE ENTRADA
# ================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = Simulador()
    ventana.show()
    sys.exit(app.exec())
