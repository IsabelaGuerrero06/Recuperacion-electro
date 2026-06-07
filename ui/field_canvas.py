import numpy as np

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient, QFont
from PyQt6.QtWidgets import QWidget

from ui.wave_canvas import _dibujar_atomo_animado, _en_resonancia


class FieldCanvas(QWidget):
    """
    Panel de campo eléctrico o magnético.
    Lee el tiempo desde el RelojGlobal compartido.
    """

    def __init__(self, atomo, reloj, incidente_func, resultante_func,
                 color, titulo, emitida_func=None):
        super().__init__()

        self.atomo           = atomo
        self.reloj           = reloj
        self.incidente_func  = incidente_func
        self.resultante_func = resultante_func
        self.emitida_func    = emitida_func
        self.color           = QColor(color)
        self.titulo          = titulo
        self.wave_mode       = "incidente_resultante"
        self.dx              = 50e-9

        reloj.suscribir(self)

    @property
    def t(self):
        return self.reloj.t

    def start(self):
        self.reloj.start()

    def pause(self):
        self.reloj.pause()

    def set_wave_mode(self, mode):
        self.wave_mode = mode
        self.update()

    def set_k(self, valor_k):
        self.atomo.set_k(valor_k)
        self.update()

    def set_n_atomos(self, n):
        pass

    def set_phase_kick(self, value):
        pass

    def _paint_absorcion(self, painter, x_px, width, height):
        painter.fillRect(x_px, 0, width - x_px, height, QColor(180, 20, 20, 35))
        painter.setPen(QPen(QColor(255, 60, 60, 200), 2))
        painter.drawLine(x_px, 0, x_px, height)
        font = QFont(); font.setPointSize(8); font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 80, 80, 200))
        painter.drawText(x_px + 8, height // 2 - 4, "ABSORBIDO")

    def paintEvent(self, event):
        painter  = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width    = self.width()
        height   = self.height()
        centro_y = height // 2
        atomo_cx = width  // 2
        t        = self.reloj.t          # tiempo compartido

        painter.fillRect(self.rect(), QColor("#101010"))
        painter.setPen(QPen(QColor("#404040"), 1))
        painter.drawLine(0, centro_y, width, centro_y)

        res = _en_resonancia(self.atomo)

        if self.wave_mode == "incidente_resultante":
            painter.setPen(QPen(self.color, 2))
            for x in range(atomo_cx - 1):
                x1 = x * self.dx; x2 = (x + 1) * self.dx
                y1 = centro_y + self.incidente_func(x1, t)
                y2 = centro_y + self.incidente_func(x2, t)
                painter.drawLine(x, int(y1), x + 1, int(y2))

            if not res:
                color_res = self.color.lighter(140)
                painter.setPen(QPen(color_res, 2))
                for x in range(atomo_cx + 1, width):
                    x1 = x * self.dx; x2 = (x + 1) * self.dx
                    y1 = centro_y + self.resultante_func(x1, t, self.atomo)
                    y2 = centro_y + self.resultante_func(x2, t, self.atomo)
                    painter.drawLine(x, int(y1), x + 1, int(y2))
        else:
            if self.wave_mode == "emitida":
                color = self.color.lighter(120)
                if self.emitida_func is None:
                    field_fn = lambda x, t_: (self.resultante_func(x, t_, self.atomo)
                                              - self.incidente_func(x, t_))
                else:
                    field_fn = lambda x, t_: self.emitida_func(x, t_, self.atomo)
            elif self.wave_mode == "resultante":
                color    = self.color.lighter(140)
                field_fn = lambda x, t_: self.resultante_func(x, t_, self.atomo)
            else:
                color    = self.color
                field_fn = self.incidente_func

            skip = res and self.wave_mode in ("resultante", "emitida")
            if not skip:
                painter.setPen(QPen(color, 2))
                start_x = atomo_cx + 1 if self.wave_mode == "resultante" else 0
                end_x   = width        if self.wave_mode == "resultante" else width - 1
                if res and self.wave_mode == "incidente":
                    end_x = atomo_cx

                for x in range(start_x, end_x):
                    if self.wave_mode == "emitida":
                        x1 = abs((x - atomo_cx) * self.dx)
                        x2 = abs((x + 1 - atomo_cx) * self.dx)
                    else:
                        x1 = x * self.dx; x2 = (x + 1) * self.dx
                    y1 = centro_y + field_fn(x1, t)
                    y2 = centro_y + field_fn(x2, t)
                    painter.drawLine(x, int(y1), x + 1, int(y2))

        # Átomo animado — mismo t compartido
        _dibujar_atomo_animado(painter, atomo_cx, centro_y, t, self.atomo)

        if res:
            self._paint_absorcion(painter, atomo_cx, width, height)

        painter.setPen(self.color)
        font = QFont(); font.setPointSize(9); font.setBold(True)
        painter.setFont(font)
        painter.drawText(8, 14, self.titulo)