import sys
import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)

from ui.wave_canvas import WaveCanvas
from physics.material import Material


class Panel(QFrame):

    def __init__(self, name=""):

        super().__init__()

        self.setFrameShape(
            QFrame.Shape.Box
        )

        self.setLineWidth(2)

        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px solid #4a4a4a;
                border-radius: 5px;
            }
        """)


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

        controles = Panel()

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

        campo_electrico = Panel()
        campo_magnetico = Panel()
        geometria = Panel()

        right_layout.addWidget(
            campo_electrico,
            3
        )

        right_layout.addWidget(
            campo_magnetico,
            3
        )

        right_layout.addWidget(
            geometria,
            3
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


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Simulador()

    ventana.show()

    sys.exit(app.exec())