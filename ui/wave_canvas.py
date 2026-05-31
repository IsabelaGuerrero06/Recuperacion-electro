import numpy as np

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QWidget

from physics.waves import (
    onda_incidente,
    onda_resultante
)


class WaveCanvas(QWidget):

    def __init__(self, material):

        super().__init__()

        self.material = material

        # ==========================
        # ESCALAS FÍSICAS
        # ==========================

        # 50 nm por pixel
        self.dx = 50e-9

        # Paso temporal base (segundos)
        self.dt = 1e-18

        # Escala de tiempo para visualizar la propagacion
        self.time_scale = 200.0

        self.t = 0.0

        self.timer = QTimer()
        self.is_running = False

        self.timer.timeout.connect(
            self.update_simulation
        )

        self.start()

    def start(self):
        if not self.timer.isActive():
            self.timer.start(16)

        self.is_running = True

    def pause(self):
        self.timer.stop()
        self.is_running = False

    def toggle(self):
        if self.is_running:
            self.pause()
        else:
            self.start()

    def update_simulation(self):
        if not self.is_running:
            return

        self.t += self.dt * self.time_scale

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        painter.fillRect(
            self.rect(),
            QColor("#101010")
        )

        centro_y = height // 2

        # ==========================
        # EJE
        # ==========================

        painter.setPen(
            QPen(QColor("#404040"), 1)
        )

        painter.drawLine(
            0,
            centro_y,
            width,
            centro_y
        )

        # ==========================
        # MATERIAL
        # ==========================

        material_x = width // 2

        painter.fillRect(
            material_x - 40,
            10,
            80,
            height - 100,
            QColor(200, 200, 200, 100)
        )

        # ==========================
        # ONDA INCIDENTE
        # ==========================

        painter.setPen(
            QPen(QColor("#00bfff"), 3)
        )

        for x in range(material_x):

            x1 = x * self.dx
            x2 = (x + 1) * self.dx

            y1 = centro_y + onda_incidente(
                x1,
                self.t
            )

            y2 = centro_y + onda_incidente(
                x2,
                self.t
            )

            painter.drawLine(
                x,
                int(y1),
                x + 1,
                int(y2)
            )

        # ==========================
        # ONDA RESULTANTE
        # ==========================

        painter.setPen(
            QPen(QColor("#00ff88"), 3)
        )

        for x in range(material_x, width):

            x1 = x * self.dx
            x2 = (x + 1) * self.dx

            y1 = centro_y + onda_resultante(
                x1,
                self.t,
                self.material
            )

            y2 = centro_y + onda_resultante(
                x2,
                self.t,
                self.material
            )

            painter.drawLine(
                x,
                int(y1),
                x + 1,
                int(y2)
            )

        # ==========================
        # INFORMACIÓN
        # ==========================

        painter.setPen(
            QColor("white")
        )

        painter.drawText(
            20,
            30,
            f"Tiempo: {self.t:.2e} s"
        )

        painter.drawText(
            20,
            50,
            f"dx: {self.dx:.2e} m/pixel"
        )

        painter.drawText(
            20,
            70,
            f"Escala tiempo: {self.time_scale:.0f}x"
        )

        painter.drawText(
            20,
            90,
            f"Material: {self.material.nombre}"
        )

        muestra_x = (material_x + 100) * self.dx

        f = onda_incidente(
            muestra_x,
            self.t
        )

        r = onda_resultante(
            muestra_x,
            self.t,
            self.material
        )

        painter.drawText(
            20,
            110,
            f"Incidente = {f:.2f}"
        )

        painter.drawText(
            20,
            130,
            f"Resultante = {r:.2f}"
        )