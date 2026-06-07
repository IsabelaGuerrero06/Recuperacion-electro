import numpy as np

from PyQt6.QtCore import QTimer, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QRadialGradient, QFont
)
from PyQt6.QtWidgets import QWidget

from physics.waves import (
    onda_incidente,
    onda_emitida,
    onda_resultante,
    amplitud_oscilacion,
    _escalar_amplitud,
    K_1,
    OMEGA_L,
)

A1 = 50.0

# Tolerancia para detectar resonancia: |ωr - ωl| / ωl < UMBRAL_RESONANCIA
UMBRAL_RESONANCIA = 0.01


def _en_resonancia(atomo):
    """
    Retorna True si el átomo está suficientemente cerca de la resonancia.
        |ωr − ωl| / ωl < UMBRAL_RESONANCIA
    """
    return abs(atomo.omega_r - OMEGA_L) / OMEGA_L < UMBRAL_RESONANCIA


def _onda_phase_kick(x, t, phase_acum):
    return A1 * np.sin(K_1 * x - OMEGA_L * t + phase_acum)


class WaveCanvas(QWidget):

    def __init__(self, atomo, n_atomos=1):
        super().__init__()
        self.atomo      = atomo
        self.n_atomos   = n_atomos
        self.phase_kick = 0.8

        self.wave_mode  = "incidente_resultante"

        self.dx         = 50e-9
        self.dt         = 1e-18
        self.time_scale = 200.0
        self.t          = 0.0

        self.timer = QTimer()
        self.is_running = False
        self.timer.timeout.connect(self.update_simulation)
        self.start()

    def set_n_atomos(self, n):
        self.n_atomos = max(1, int(n))
        self.update()

    def set_phase_kick(self, value):
        self.phase_kick = float(value)
        self.update()

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

    def set_wave_mode(self, mode):
        self.wave_mode = mode
        self.update()

    def sample_x(self):
        width = self.width()
        if width <= 0:
            return 0.0
        return (width // 2 + 100) * self.dx

    def _posiciones_atomos_px(self, width):
        if self.n_atomos == 1:
            return [width // 2]
        margen = width // 6
        zona   = width - margen
        paso   = zona / self.n_atomos
        return [int(margen + paso * (i + 0.5)) for i in range(self.n_atomos)]

    # ----------------------------------------------------------
    # paintEvent
    # ----------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width    = self.width()
        height   = self.height()
        centro_y = height // 2

        painter.fillRect(self.rect(), QColor("#101010"))
        painter.setPen(QPen(QColor("#404040"), 1))
        painter.drawLine(0, centro_y, width, centro_y)

        resonancia = _en_resonancia(self.atomo)

        if self.wave_mode == "phase_kick":
            self._paint_phase_kick(painter, width, centro_y, resonancia)
        elif self.wave_mode == "incidente_resultante":
            self._paint_multicapa(painter, width, centro_y, resonancia)
        else:
            self._paint_modo_unico(painter, width, centro_y, resonancia)

        self._paint_leyenda(painter, resonancia)

    # ----------------------------------------------------------
    # Indicador de absorción — se llama desde cualquier modo
    # ----------------------------------------------------------

    def _paint_absorcion(self, painter, x_atomo_px, width, height):
        """
        Dibuja una zona roja semitransparente después del átomo
        y el texto ABSORCIÓN.
        """
        # Zona roja de absorción
        painter.fillRect(
            x_atomo_px, 0,
            width - x_atomo_px, height,
            QColor(180, 20, 20, 35),
        )
        # Línea vertical roja en el átomo
        painter.setPen(QPen(QColor(255, 60, 60, 200), 2))
        painter.drawLine(x_atomo_px, 0, x_atomo_px, height)

        # Texto
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 80, 80, 220))
        painter.drawText(
            x_atomo_px + 20,
            height // 2 - 10,
            "ABSORCIÓN  (ωr ≈ ωl)",
        )
        font2 = QFont()
        font2.setPointSize(9)
        painter.setFont(font2)
        painter.setPen(QColor(255, 140, 140, 180))
        painter.drawText(
            x_atomo_px + 20,
            height // 2 + 12,
            "La onda no se propaga más allá del material",
        )

    # ----------------------------------------------------------
    # phase_kick
    # ----------------------------------------------------------

    def _paint_phase_kick(self, painter, width, centro_y, resonancia):
        atomos_px = self._posiciones_atomos_px(width)
        N         = len(atomos_px)
        bordes    = [0] + atomos_px + [width]

        # En resonancia: solo dibujamos el segmento 0 (antes del primer átomo)
        n_segmentos = 1 if resonancia else N + 1

        for i in range(n_segmentos):
            px_start   = bordes[i]
            px_end     = bordes[i + 1]
            phase_acum = i * self.phase_kick

            painter.setPen(QPen(QColor("#ffdd00"), 2))
            for px in range(px_start, min(px_end, width - 1)):
                x1 = px       * self.dx
                x2 = (px + 1) * self.dx
                y1 = centro_y + _onda_phase_kick(x1, self.t, phase_acum)
                y2 = centro_y + _onda_phase_kick(x2, self.t, phase_acum)
                painter.drawLine(px, int(y1), px + 1, int(y2))

        painter.setPen(QPen(QColor(100, 180, 255, 160), 1))
        for px in atomos_px:
            painter.drawLine(px, 0, px, self.height())

        radio = 8 if N > 5 else 14
        for px in atomos_px:
            _dibujar_atomo_estatico(painter, px, centro_y, "", radio)

        if resonancia:
            self._paint_absorcion(painter, atomos_px[0], width, self.height())

    # ----------------------------------------------------------
    # incidente_resultante multicapa
    # ----------------------------------------------------------

    def _paint_multicapa(self, painter, width, centro_y, resonancia):
        atomos_px = self._posiciones_atomos_px(width)
        N         = len(atomos_px)

        C_inc = np.array([0x00, 0xff, 0x88])
        C_res = np.array([0xcf, 0xe9, 0x66])

        # Onda incidente antes del primer átomo — siempre
        painter.setPen(QPen(QColor("#00ff88"), 2))
        for px in range(atomos_px[0]):
            x1 = px       * self.dx
            x2 = (px + 1) * self.dx
            y1 = centro_y + onda_incidente(x1, self.t)
            y2 = centro_y + onda_incidente(x2, self.t)
            painter.drawLine(px, int(y1), px + 1, int(y2))

        # Si NO hay resonancia: dibujamos la onda resultante por segmento
        if not resonancia:
            for i in range(N):
                px_start = atomos_px[i]
                px_end   = atomos_px[i + 1] if i + 1 < N else width
                alpha    = i / max(N - 1, 1)
                rgb      = ((1 - alpha) * C_inc + alpha * C_res).astype(int)
                color    = QColor(int(rgb[0]), int(rgb[1]), int(rgb[2]))
                painter.setPen(QPen(color, 2))

                for px in range(px_start, min(px_end, width - 1)):
                    x1 = px       * self.dx
                    x2 = (px + 1) * self.dx
                    y1 = centro_y + onda_resultante(x1, self.t, self.atomo)
                    y2 = centro_y + onda_resultante(x2, self.t, self.atomo)
                    painter.drawLine(px, int(y1), px + 1, int(y2))

        radio = 10 if N > 5 else 16
        for px in atomos_px:
            _dibujar_atomo_estatico(
                painter, px, centro_y,
                "" if N > 1 else self.atomo.nombre, radio,
            )

        painter.setPen(QPen(QColor(70, 70, 70, 90), 1))
        for px in atomos_px:
            painter.drawLine(px, 0, px, self.height())

        if resonancia:
            self._paint_absorcion(painter, atomos_px[0], width, self.height())

    # ----------------------------------------------------------
    # Modos simples
    # ----------------------------------------------------------

    def _paint_modo_unico(self, painter, width, centro_y, resonancia):
        atomo_cx = width // 2

        if self.wave_mode == "emitida":
            color = QColor("#ffcc66")
            def wave_fn(x, t):
                return onda_emitida(abs(x), t, self.atomo)
        elif self.wave_mode == "resultante":
            color = QColor("#cfe966")
            wave_fn = lambda x, t: onda_resultante(x, t, self.atomo)
        else:
            color = QColor("#00ff88")
            wave_fn = onda_incidente

        painter.setPen(QPen(color, 3))

        # En resonancia: modos que muestran la zona derecha no dibujan nada ahí
        if resonancia and self.wave_mode in ("resultante", "emitida"):
            # Solo dibujamos el átomo y el indicador — sin onda
            _dibujar_atomo_estatico(painter, atomo_cx, centro_y, self.atomo.nombre)
            self._paint_absorcion(painter, atomo_cx, width, self.height())
            return

        # Modo incidente en resonancia: dibujamos solo la mitad izquierda
        if resonancia and self.wave_mode == "incidente":
            for px in range(atomo_cx):
                x1 = px       * self.dx
                x2 = (px + 1) * self.dx
                y1 = centro_y + wave_fn(x1, self.t)
                y2 = centro_y + wave_fn(x2, self.t)
                painter.drawLine(px, int(y1), px + 1, int(y2))
            _dibujar_atomo_estatico(painter, atomo_cx, centro_y, self.atomo.nombre)
            self._paint_absorcion(painter, atomo_cx, width, self.height())
            return

        # Caso normal — sin resonancia
        start_x = atomo_cx + 1 if self.wave_mode == "resultante" else 0
        end_x   = width        if self.wave_mode == "resultante" else width - 1

        for px in range(start_x, end_x):
            if self.wave_mode == "emitida":
                x1 = (px - atomo_cx) * self.dx
                x2 = (px + 1 - atomo_cx) * self.dx
            else:
                x1 = px       * self.dx
                x2 = (px + 1) * self.dx
            y1 = centro_y + wave_fn(x1, self.t)
            y2 = centro_y + wave_fn(x2, self.t)
            painter.drawLine(px, int(y1), px + 1, int(y2))

        _dibujar_atomo_estatico(painter, atomo_cx, centro_y, self.atomo.nombre)

    # ----------------------------------------------------------
    # Leyenda
    # ----------------------------------------------------------

    def _paint_leyenda(self, painter, resonancia):
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        if resonancia:
            # La leyenda de absorción domina — solo añadimos la línea de modo
            painter.setPen(QColor("#00ff88"))
            painter.drawText(20, 20, "── Onda incidente")
            painter.setPen(QColor(255, 80, 80))
            painter.drawText(20, 38, "✕  Onda absorbida  (ωr = ωl)")
            return

        if self.wave_mode == "phase_kick":
            painter.setPen(QColor("#ffdd00"))
            painter.drawText(20, 20, "── Phase kick  (estilo 3B1B)")
            painter.setPen(QColor("#ff6666"))
            painter.drawText(20, 38, f"Phase kick = {self.phase_kick:.2f} rad")
            painter.setPen(QColor("#aaaaaa"))
            painter.drawText(20, 56, f"N = {self.n_atomos} átomos")
        elif self.wave_mode == "incidente_resultante":
            painter.setPen(QColor("#00ff88"))
            painter.drawText(20, 20, "── Onda incidente")
            painter.setPen(QColor("#cfe966"))
            painter.drawText(20, 38, "── Onda resultante  (por segmento)")
            painter.setPen(QColor("#aaaaaa"))
            painter.drawText(20, 56,
                f"N = {self.n_atomos}  |  "
                f"A_x = {_escalar_amplitud(amplitud_oscilacion(self.atomo)):.1f} px")
        elif self.wave_mode == "emitida":
            painter.setPen(QColor("#ffcc66"))
            painter.drawText(20, 20, "── Onda emitida")
        elif self.wave_mode == "resultante":
            painter.setPen(QColor("#cfe966"))
            painter.drawText(20, 20, "── Onda resultante")
        else:
            painter.setPen(QColor("#00ff88"))
            painter.drawText(20, 20, "── Onda incidente")

        if self.wave_mode not in ("incidente_resultante", "phase_kick"):
            painter.setPen(QColor("#aaaaaa"))
            A_vis = _escalar_amplitud(amplitud_oscilacion(self.atomo))
            painter.drawText(20, 56, f"Átomo: {self.atomo.nombre}  |  A_x = {A_vis:.1f} px")


# ================================================================
# ÁTOMO ESTÁTICO
# ================================================================

def _dibujar_atomo_estatico(painter, cx, cy, nombre="", radio=16):
    R = radio

    grad = QRadialGradient(QPointF(cx - 4, cy - 4), R)
    grad.setColorAt(0.0, QColor(160, 210, 255, 200))
    grad.setColorAt(0.6, QColor( 60, 130, 220, 160))
    grad.setColorAt(1.0, QColor( 20,  60, 160, 100))
    painter.setBrush(QBrush(grad))
    painter.setPen(QPen(QColor(120, 180, 255, 180), 1))
    painter.drawEllipse(cx - R, cy - R, R * 2, R * 2)

    r_centro = max(3, R // 4)
    painter.setBrush(QBrush(QColor(255, 220, 120, 230)))
    painter.setPen(QPen(QColor(255, 180, 60, 200), 1))
    painter.drawEllipse(cx - r_centro, cy - r_centro,
                        r_centro * 2, r_centro * 2)

    if nombre:
        painter.setPen(QColor("#999999"))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        fm_w = len(nombre) * 5
        painter.drawText(cx - fm_w, cy + R + 14, nombre)