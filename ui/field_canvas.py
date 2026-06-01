import numpy as np

from PyQt6.QtCore import QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient, QFont
from PyQt6.QtWidgets import QWidget

from ui.wave_canvas import _dibujar_atomo_estatico


class FieldCanvas(QWidget):
    """
    Panel de campo eléctrico o magnético.

    Campo incidente → átomo (estático) → campo resultante
    """

    def __init__(self, atomo, incidente_func, resultante_func, color, titulo):
        super().__init__()

        self.atomo          = atomo
        self.incidente_func = incidente_func
        self.resultante_func = resultante_func
        self.color          = QColor(color)
        self.titulo         = titulo

        self.dx         = 50e-9
        self.dt         = 1e-18
        self.time_scale = 200
        self.t          = 0.0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(16)
        self.is_running = True

    def start(self):
        if not self.timer.isActive():
            self.timer.start(16)
        self.is_running = True

    def pause(self):
        self.timer.stop()
        self.is_running = False

    def update_simulation(self):
        self.t += self.dt * self.time_scale
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width    = self.width()
        height   = self.height()
        centro_y = height // 2
        atomo_cx = width  // 2

        # Fondo
        painter.fillRect(self.rect(), QColor("#101010"))

        # Eje
        painter.setPen(QPen(QColor("#404040"), 1))
        painter.drawLine(0, centro_y, width, centro_y)

        # ── Campo incidente (izquierda) ──────────────────────
        painter.setPen(QPen(self.color, 2))
        for x in range(atomo_cx - 1):
            x1 = x       * self.dx
            x2 = (x + 1) * self.dx
            y1 = centro_y + self.incidente_func(x1, self.t)
            y2 = centro_y + self.incidente_func(x2, self.t)
            painter.drawLine(x, int(y1), x + 1, int(y2))

        # ── Campo resultante (derecha) ───────────────────────
        color_res = self.color.lighter(140)
        painter.setPen(QPen(color_res, 2))
        for x in range(atomo_cx + 1, width):
            x1 = x       * self.dx
            x2 = (x + 1) * self.dx
            y1 = centro_y + self.resultante_func(x1, self.t, self.atomo)
            y2 = centro_y + self.resultante_func(x2, self.t, self.atomo)
            painter.drawLine(x, int(y1), x + 1, int(y2))

        # ── Átomo estático en el centro ──────────────────────
        _dibujar_atomo_estatico(painter, atomo_cx, centro_y)

        # ── Título ───────────────────────────────────────────
        painter.setPen(self.color)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(8, 14, self.titulo)
