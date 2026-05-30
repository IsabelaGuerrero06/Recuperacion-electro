import numpy as np

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget


class WaveCanvas(QWidget):

    def __init__(self):
        super().__init__()

        self.t = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(16)  # ~60 FPS

    def update_wave(self):
        self.t += 0.1
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        painter.fillRect(self.rect(), QColor("#151515"))

        # Línea central
        painter.setPen(QPen(QColor("#404040"), 1))
        painter.drawLine(0, height // 2, width, height // 2)

        # Onda
        pen = QPen(QColor("#00d4ff"), 3)
        painter.setPen(pen)

        points = []

        for x in range(width):

            amplitud = 80
            k = 0.03      # número de onda
            w = 0.20      # velocidad

            y = height/2 + amplitud * np.sin(k*x - w*self.t)

            points.append((x, y))

        for i in range(len(points) - 1):

            painter.drawLine(
                int(points[i][0]),
                int(points[i][1]),
                int(points[i + 1][0]),
                int(points[i + 1][1]),
            )