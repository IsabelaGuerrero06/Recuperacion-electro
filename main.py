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
from physics.material import Material
from ui.field_canvas import FieldCanvas

from physics.waves import (
    campo_electrico_incidente,
    campo_electrico_resultante,
    campo_magnetico_incidente,
    campo_magnetico_resultante,
)


from models.sidebar import CalculationSidebar
from models.panel import Panel

def B_incidente_visual(x, t):
    return campo_magnetico_incidente(x, t) * 3e8


def B_resultante_visual(x, t, material):
    return campo_magnetico_resultante(
        x,
        t,
        material
    ) * 3e8

class Simulador(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Simulador Radiación-Materia"
        )

        self.resize(1400, 800)

        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
            }
        """)

        main_layout = QHBoxLayout(self)

        # ==========================
        # MATERIAL
        # ==========================

        vidrio = Material(
            nombre="Vidrio",
            indice_refraccion=1.5,
            amplitud_generada=25,
            fase=np.pi / 4
        )

        # ==========================
        # PANEL IZQUIERDO
        # ==========================

        left_layout = QVBoxLayout()

        simulacion = WaveCanvas(
            vidrio
        )
        campo_electrico = FieldCanvas(
            material=vidrio,
            incidente_func=campo_electrico_incidente,
            resultante_func=campo_electrico_resultante,
            color="#00bfff",
            titulo="Campo Eléctrico E(x,t)"
        )
        campo_magnetico = FieldCanvas(
                material=vidrio,
                incidente_func=B_incidente_visual,
                resultante_func=B_resultante_visual,
                color="#ff4477",
                titulo="Campo Magnético B(x,t)"
            )

        self.simulaciones = [
            simulacion, campo_electrico, campo_magnetico
        ]

        self.is_paused = False

        controles = Panel()

        controles_layout = QVBoxLayout(controles)
        controles_layout.setContentsMargins(12, 12, 12, 12)
        controles_layout.setSpacing(10)

        self.estado_simulacion = QLabel(
            "Simulacion: Activa"
        )

        self.estado_simulacion.setStyleSheet(
            "color: #e0e0e0;"
        )

        self.toggle_btn = QPushButton(
            "Pausar"
        )

        self.toggle_sidebar_btn = QPushButton(
            "Ocultar calculos"
        )

        self.toggle_btn.clicked.connect(
            self.toggle_simulacion
        )

        self.toggle_sidebar_btn.clicked.connect(
            self.toggle_sidebar
        )

        controles_layout.addWidget(
            self.estado_simulacion
        )

        controles_layout.addWidget(
            self.toggle_btn
        )

        controles_layout.addWidget(
            self.toggle_sidebar_btn
        )

        controles_layout.addStretch(1)

        left_layout.addWidget(
            simulacion,
            7
        )

        left_layout.addWidget(
            controles,
            3
        )

        # ==========================
        # PANEL DERECHO
        # ==========================

        right_layout = QVBoxLayout()

        self.sidebar = CalculationSidebar(
            simulacion,
            vidrio
        )

        self.simulaciones.append(self.sidebar)

        right_layout.addWidget(
            campo_electrico,
            3
        )

        right_layout.addWidget(
            campo_magnetico,
            3
        )

        right_layout.addWidget(
            self.sidebar,
            4
        )

        # ==========================
        # DISTRIBUCIÓN
        # ==========================

        main_layout.addLayout(
            left_layout,
            7
        )

        main_layout.addLayout(
            right_layout,
            3
        )

    def toggle_simulacion(self):
        if self.is_paused:
            for simulacion in self.simulaciones:
                simulacion.start()

            self.estado_simulacion.setText(
                "Simulacion: Activa"
            )

            self.toggle_btn.setText(
                "Pausar"
            )

            self.is_paused = False
        else:
            for simulacion in self.simulaciones:
                simulacion.pause()

            self.estado_simulacion.setText(
                "Simulacion: Pausada"
            )

            self.toggle_btn.setText(
                "Reanudar"
            )

            self.is_paused = True

    def toggle_sidebar(self):
        visible = self.sidebar.isVisible()
        self.sidebar.setVisible(not visible)

        if visible:
            self.toggle_sidebar_btn.setText(
                "Mostrar calculos"
            )
        else:
            self.toggle_sidebar_btn.setText(
                "Ocultar calculos"
            )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Simulador()

    ventana.show()

    sys.exit(app.exec())