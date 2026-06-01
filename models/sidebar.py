import math
import numpy as np

from physics.waves_no_scale import (
    C, K_1, LAMBDA_1, OMEGA_1,
    campo_electrico_emitido,
    campo_electrico_incidente,
    campo_electrico_resultante,
    campo_magnetico_emitido,
    campo_magnetico_incidente,
    campo_magnetico_resultante,
    onda_incidente,
    onda_emitida,
    amplitud_oscilacion_real,
)

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QRadialGradient, QFont
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QLabel, QScrollArea,
)

from models.panel import Panel


class CalculationSidebar(Panel):
    """
    Panel inferior derecho.
    Muestra cálculos del modelo de Lorentz + animación del electrón.
    El electrón animado SOLO existe aquí.
    """

    def __init__(self, wave_canvas, atomo):
        super().__init__()

        self.wave_canvas = wave_canvas
        self.atomo       = atomo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Modelo de Lorentz — Cálculos")
        title.setStyleSheet(
            "color: #ffffff; font-weight: bold; font-size: 13px;"
        )
        layout.addWidget(title)

        # ── Widget animado (solo aquí) ────────────────────────
        self.electron_anim = ElectronAnimation(atomo)
        self.electron_anim.setFixedHeight(90)
        layout.addWidget(self.electron_anim)

        # ── Texto de cálculos ─────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        self.lorentz_label = QLabel()
        self.onda_label    = QLabel()
        self.campo_e_label = QLabel()
        self.campo_b_label = QLabel()

        for label in [
            self.lorentz_label,
            self.onda_label,
            self.campo_e_label,
            self.campo_b_label,
        ]:
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            label.setStyleSheet(
                "color: #e0e0e0; font-family: Consolas; font-size: 11px;"
            )

        content_layout.addWidget(self.lorentz_label)
        content_layout.addWidget(self.onda_label)
        content_layout.addWidget(self.campo_e_label)
        content_layout.addWidget(self.campo_b_label)
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        scroll.setStyleSheet("background: transparent;")

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
        self.electron_anim.start()

    def pause(self):
        self.timer.stop()
        self.is_running = False
        self.electron_anim.pause()

    def _fmt(self, value):
        return f"{value:.3e}"

    def update_values(self):
        x = self.wave_canvas.sample_x()
        t = self.wave_canvas.t
        a = self.atomo

        omega_r = a.omega_r
        A_x     = amplitud_oscilacion_real(a)

        f_inc  = onda_incidente(x, t)
        f_emit = onda_emitida(x, t, a)
        f_res  = f_inc + f_emit

        E_inc  = campo_electrico_incidente(x, t)
        E_emit = campo_electrico_emitido(x, t, a)
        E_res  = E_inc + E_emit

        B_inc  = campo_magnetico_incidente(x, t)
        B_emit = campo_magnetico_emitido(x, t, a)
        B_res  = B_inc + B_emit

        self.lorentz_label.setText("<br>".join([
            "<span style='color:#ffd166;font-weight:bold;'>Modelo de Lorentz</span>",
            "─────────────────────────────────────",
            "ωr = √(k/m)",
            f"  m  = {self._fmt(a.m)} kg",
            f"  q  = {self._fmt(a.q)} C",
            f"  k  = {self._fmt(a.k)} N/m",
            f"  ωr = {self._fmt(omega_r)} rad/s",
            f"  ωl = {self._fmt(OMEGA_1)} rad/s",
            "",
            "A_x = qE0 / (m·(ωr² − ωl²))",
            f"  A_x = {self._fmt(A_x)} m",
            f"  x = {self._fmt(x)} m   t = {self._fmt(t)} s",
        ]))

        self.onda_label.setText("<br>".join([
            "<span style='color:#00ff88;font-weight:bold;'>Ondas</span>",
            "─────────────────────────────────────",
            "f(x,t) = A1·sin(k·x − ωl·t)",
            f"  f = {self._fmt(f_inc)}",
            "g(x,t) = A_x·sin(k·x − ωl·t + φ)",
            f"  g = {self._fmt(f_emit)}",
            "r = f + g",
            f"  r = {self._fmt(f_res)}",
        ]))

        self.campo_e_label.setText("<br>".join([
            "<span style='color:#7ad1ff;font-weight:bold;'>Campo Eléctrico</span>",
            "─────────────────────────────────────",
            "E_inc  = E0·cos(k·x − ωl·t)",
            f"  E_inc  = {self._fmt(E_inc)} V/m",
            "E_emit = A_x·cos(k·x − ωl·t + φ)",
            f"  E_emit = {self._fmt(E_emit)} V/m",
            f"  E_res  = {self._fmt(E_res)} V/m",
        ]))

        B0 = 50 / C
        self.campo_b_label.setText("<br>".join([
            "<span style='color:#ff7aa2;font-weight:bold;'>Campo Magnético</span>",
            "─────────────────────────────────────",
            "B_inc  = (E0/c)·cos(k·x − ωl·t)",
            f"  B0 = {self._fmt(B0)} T",
            f"  B_inc  = {self._fmt(B_inc)} T",
            f"  B_emit = {self._fmt(B_emit)} T",
            f"  B_res  = {self._fmt(B_res)} T",
        ]))


# ================================================================
# WIDGET: Electrón animado — SOLO en el sidebar
# ================================================================

class ElectronAnimation(QWidget):
    """
    Electrón oscilando sobre el átomo.
    Muestra ωr y A_x en tiempo real.
    """

    def __init__(self, atomo):
        super().__init__()
        self.atomo = atomo
        self.t     = 0.0

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def start(self):
        if not self.timer.isActive():
            self.timer.start(16)

    def pause(self):
        self.timer.stop()

    def _tick(self):
        self.t += 1e-18 * 200
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        painter.fillRect(self.rect(), QColor("#181818"))

        cx = w // 4        # átomo en el cuarto izquierdo
        cy = h // 2

        a = self.atomo
        A_x_real = amplitud_oscilacion_real(a)

        # Escalar oscilación visual (máx ±30 px)
        max_px   = 28
        A_px     = float(np.clip(A_x_real * 1e28, -max_px, max_px))
        osc_y    = int(A_px * math.cos(OMEGA_1 * self.t))

        angulo = OMEGA_1 * self.t
        ex = cx + int(22 * math.cos(angulo))
        ey = cy + int(13 * math.sin(angulo)) + osc_y

        # Órbita
        painter.setPen(QPen(QColor(100, 150, 200, 100), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawEllipse(cx - 24, cy - 14, 48, 28)

        # Núcleo
        gn = QRadialGradient(QPointF(cx, cy), 10)
        gn.setColorAt(0, QColor("#ff9944"))
        gn.setColorAt(1, QColor("#cc3300"))
        painter.setBrush(QBrush(gn))
        painter.setPen(QPen(QColor("#ff6622"), 1))
        painter.drawEllipse(cx - 10, cy - 10, 20, 20)

        # Electrón
        ge = QRadialGradient(QPointF(ex, ey), 5)
        ge.setColorAt(0, QColor("#88ddff"))
        ge.setColorAt(1, QColor("#0066cc"))
        painter.setBrush(QBrush(ge))
        painter.setPen(QPen(QColor("#00aaff"), 1))
        painter.drawEllipse(ex - 5, ey - 5, 10, 10)

        # Fórmulas a la derecha del átomo
        font = QFont("Consolas", 9)
        painter.setFont(font)
        x_txt = cx + 45

        painter.setPen(QColor("#ffd166"))
        painter.drawText(x_txt, cy - 22, "ωr = √(k/m)")
        painter.setPen(QColor("#aaaaaa"))
        painter.drawText(x_txt, cy - 8,  f"   = {a.omega_r:.3e} rad/s")

        painter.setPen(QColor("#88ddff"))
        painter.drawText(x_txt, cy + 10, "A_x = qE0/(m(ωr²−ωl²))")
        painter.setPen(QColor("#aaaaaa"))
        painter.drawText(x_txt, cy + 24, f"    = {A_x_real:.3e} m")
