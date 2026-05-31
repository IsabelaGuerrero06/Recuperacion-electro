import numpy as np

from physics.waves import (
    C,
    K_1,
    LAMBDA_VISUAL,
    OMEGA_1,
    campo_electrico_material,
    campo_electrico_incidente,
    campo_electrico_resultante,
    campo_magnetico_material,
    campo_magnetico_incidente,
    campo_magnetico_resultante,
    onda_incidente,
    onda_material
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QLabel,
    QScrollArea,
)

from models.panel import Panel

class CalculationSidebar(Panel):

    def __init__(self, wave_canvas, material):

        super().__init__()

        self.wave_canvas = wave_canvas
        self.material = material

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Calculos sincronizados")
        title.setStyleSheet(
            "color: #ffffff; font-weight: bold;"
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.onda_label = QLabel()
        self.campo_e_label = QLabel()
        self.campo_b_label = QLabel()

        for label in [
            self.onda_label,
            self.campo_e_label,
            self.campo_b_label
        ]:
            label.setWordWrap(True)
            label.setTextFormat(
                Qt.TextFormat.RichText
            )
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            label.setStyleSheet(
                "color: #e0e0e0; font-family: Consolas; font-size: 12px;"
            )

        content_layout.addWidget(self.onda_label)
        content_layout.addWidget(self.campo_e_label)
        content_layout.addWidget(self.campo_b_label)
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)

        layout.addWidget(title)
        layout.addWidget(scroll, 1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_values)
        self.timer.start(100)
        self.is_running = True

        self.update_values()

    def start(self):
        if not self.timer.isActive():
            self.timer.start(100)

        self.is_running = True

    def pause(self):
        self.timer.stop()
        self.is_running = False

    def _fmt(self, value):
        return f"{value:.3e}"

    def update_values(self):
        x = self.wave_canvas.sample_x()
        t = self.wave_canvas.t

        lambda_2 = LAMBDA_VISUAL / self.material.n
        k_2 = 2 * np.pi / lambda_2

        f_inc = onda_incidente(x, t)
        f_mat = onda_material(x, t, self.material)
        f_res = f_inc + f_mat

        E_inc = campo_electrico_incidente(x, t)
        E_mat = campo_electrico_material(x, t, self.material)
        E_res = E_inc + E_mat

        B_inc = campo_magnetico_incidente(x, t)
        B_mat = campo_magnetico_material(x, t, self.material)
        B_res = B_inc + B_mat


        onda_text = "<br>".join([
            "<span style='color:#ffd166; font-weight:bold;'>Onda principal</span>",
            "Formula: f(x,t)=A*sin(k*x - omega*t + phi)",
            "Reemplazo: A=50, phi=0",
            f"k={self._fmt(K_1)}, omega={self._fmt(OMEGA_1)}",
            f"x={self._fmt(x)} m, t={self._fmt(t)} s",
            f"f(x,t)={self._fmt(f_inc)}",
            "<span style='color:#9fb4c8; font-weight:bold;'>Material</span>",
            f"A2={self._fmt(self.material.A2)}, phi2={self._fmt(self.material.phi2)}",
            f"k2={self._fmt(k_2)}, omega2={self._fmt(OMEGA_1)}",
            f"g(x,t)={self._fmt(f_mat)}",
            f"Resultante r=f+g={self._fmt(f_res)}"
        ])

        e_text = "<br>".join([
            "<span style='color:#7ad1ff; font-weight:bold;'>Campo electrico</span>",
            "Formula: E(x,t)=E0*cos(k*x - omega*t + phi)",
            "Reemplazo: E0=50, phi=0",
            f"k={self._fmt(K_1)}, omega={self._fmt(OMEGA_1)}",
            f"x={self._fmt(x)} m, t={self._fmt(t)} s",
            f"E(x,t)={self._fmt(E_inc)}",
            "<span style='color:#9fb4c8; font-weight:bold;'>Material</span>",
            f"E0_2={self._fmt(self.material.A2)}, phi2={self._fmt(self.material.phi2)}",
            f"k2={self._fmt(k_2)}, omega2={self._fmt(OMEGA_1)}",
            f"E2(x,t)={self._fmt(E_mat)}",
            f"Resultante E=E+E2={self._fmt(E_res)}"
        ])

        B0 = 50 / C
        velocidad_material = C / self.material.n
        B0_material = self.material.A2 / velocidad_material

        b_text = "<br>".join([
            "<span style='color:#ff7aa2; font-weight:bold;'>Campo magnetico</span>",
            "Formula: B(x,t)=B0*cos(k*x - omega*t + phi)",
            f"Reemplazo: B0=E0/C={self._fmt(B0)}, phi=0",
            f"k={self._fmt(K_1)}, omega={self._fmt(OMEGA_1)}",
            f"x={self._fmt(x)} m, t={self._fmt(t)} s",
            f"B(x,t)={self._fmt(B_inc)}",
            "<span style='color:#9fb4c8; font-weight:bold;'>Material</span>",
            f"B0_2=E0_2/v={self._fmt(B0_material)}, phi2={self._fmt(self.material.phi2)}",
            f"k2={self._fmt(k_2)}, omega2={self._fmt(OMEGA_1)}",
            f"B2(x,t)={self._fmt(B_mat)}",
            f"Resultante B=B+B2={self._fmt(B_res)}"
        ])

        self.onda_label.setText(onda_text)
        self.campo_e_label.setText(e_text)
        self.campo_b_label.setText(b_text)

