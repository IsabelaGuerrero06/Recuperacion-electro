import numpy as np

from PyQt6.QtCore import QTimer, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QRadialGradient, QFont
)
from PyQt6.QtWidgets import QWidget

from physics.waves import (
    onda_incidente,
    onda_resultante,
    amplitud_oscilacion,
    _escalar_amplitud,
)


class WaveCanvas(QWidget):
    """
    Panel principal de ondas.

    Zona izquierda : onda incidente  f(x,t) = A1·sin(k·x − ωl·t)
    Centro         : átomo estático (símbolo simple)
    Zona derecha   : onda resultante r(x,t) = f(x,t) + g(x,t)
    """

    def __init__(self, atomo):
        super().__init__()
        self.atomo = atomo

        self.dx         = 50e-9
        self.dt         = 1e-18
        self.time_scale = 200.0
        self.t          = 0.0

        self.timer = QTimer()
        self.is_running = False
        self.timer.timeout.connect(self.update_simulation)
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

    def sample_x(self):
        width = self.width()
        if width <= 0:
            return 0.0
        return (width // 2 + 100) * self.dx

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

        # ── Onda incidente (izquierda) ───────────────────────
        painter.setPen(QPen(QColor("#00ff88"), 3))
        for x in range(atomo_cx - 1):
            x1 = x       * self.dx
            x2 = (x + 1) * self.dx
            y1 = centro_y + onda_incidente(x1, self.t)
            y2 = centro_y + onda_incidente(x2, self.t)
            painter.drawLine(x, int(y1), x + 1, int(y2))

        # ── Onda resultante (derecha) ────────────────────────
        painter.setPen(QPen(QColor("#cfe966"), 3))
        for x in range(atomo_cx + 1, width):
            x1 = x       * self.dx
            x2 = (x + 1) * self.dx
            y1 = centro_y + onda_resultante(x1, self.t, self.atomo)
            y2 = centro_y + onda_resultante(x2, self.t, self.atomo)
            painter.drawLine(x, int(y1), x + 1, int(y2))

        # ── Átomo estático ───────────────────────────────────
        _dibujar_atomo_estatico(painter, atomo_cx, centro_y, self.atomo.nombre)

        # ── Leyenda ──────────────────────────────────────────
        painter.setPen(QColor("#00ff88"))
        painter.drawText(20, 20, "── Onda incidente")
        painter.setPen(QColor("#cfe966"))
        painter.drawText(20, 38, "── Onda resultante")
        painter.setPen(QColor("#aaaaaa"))
        A_vis = _escalar_amplitud(amplitud_oscilacion(self.atomo))
        painter.drawText(20, 56, f"Átomo: {self.atomo.nombre}  |  A_x = {A_vis:.1f} px")


# ================================================================
# ÁTOMO ESTÁTICO — compartido por los tres paneles de onda
# ================================================================

def _dibujar_atomo_estatico(painter, cx, cy, nombre=""):
    """
    Dibuja un átomo simple y estático: solo un círculo con un punto
    central. Sin órbita, sin electrón animado, sin halo.
    La onda llega desde la izquierda y sale por la derecha.
    """
    R = 16   # radio del átomo

    # Cuerpo del átomo — círculo semitransparente
    grad = QRadialGradient(QPointF(cx - 4, cy - 4), R)
    grad.setColorAt(0.0, QColor(160, 210, 255, 200))
    grad.setColorAt(0.6, QColor( 60, 130, 220, 160))
    grad.setColorAt(1.0, QColor( 20,  60, 160, 100))
    painter.setBrush(QBrush(grad))
    painter.setPen(QPen(QColor(120, 180, 255, 180), 1))
    painter.drawEllipse(cx - R, cy - R, R * 2, R * 2)

    # Punto central (núcleo simplificado)
    r_centro = 4
    painter.setBrush(QBrush(QColor(255, 220, 120, 230)))
    painter.setPen(QPen(QColor(255, 180, 60, 200), 1))
    painter.drawEllipse(cx - r_centro, cy - r_centro,
                        r_centro * 2, r_centro * 2)

    # Nombre del átomo debajo
    if nombre:
        painter.setPen(QColor("#999999"))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        fm_w = len(nombre) * 5          # aproximación del ancho del texto
        painter.drawText(cx - fm_w, cy + R + 14, nombre)
