import cmath
import numpy as np

from PyQt6.QtCore import QPointF
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
    _escalar_amplitud_con_atomo,
    phi_emision,
    K_1,
    OMEGA_L,
)

A1 = 50.0
MAX_OSC_PX      = 40.0
UMBRAL_RESONANCIA = 0.01


def _en_resonancia(atomo):
    return abs(atomo.omega_r - OMEGA_L) / OMEGA_L < UMBRAL_RESONANCIA


def _offset_atomo(t, atomo):
    """Desplazamiento vertical del átomo en px: A_x_vis · cos(ωl·t)."""
    A_x_fis = amplitud_oscilacion(atomo)
    A_x_vis = _escalar_amplitud_con_atomo(A_x_fis, atomo)
    A_norm  = float(np.clip(A_x_vis / 120.0 * MAX_OSC_PX,
                            -MAX_OSC_PX, MAX_OSC_PX))
    return A_norm * np.cos(OMEGA_L * t)


def _onda_phase_kick(x, t, phase_acum):
    return A1 * np.sin(K_1 * x - OMEGA_L * t + phase_acum)


# ================================================================
# ÁTOMO ANIMADO — compartido por los tres paneles
# ================================================================

def _dibujar_atomo_animado(painter, cx, cy, t, atomo, nombre="", radio=16):
    offset  = int(_offset_atomo(t, atomo))
    cy_anim = cy + offset
    R = radio

    # Guía de recorrido
    painter.setPen(QPen(QColor(255, 200, 100, 50), 1))
    painter.drawLine(cx, cy - int(MAX_OSC_PX) - R,
                     cx, cy + int(MAX_OSC_PX) + R)

    # Cuerpo
    grad = QRadialGradient(QPointF(cx - 4, cy_anim - 4), R)
    grad.setColorAt(0.0, QColor(160, 210, 255, 200))
    grad.setColorAt(0.6, QColor( 60, 130, 220, 160))
    grad.setColorAt(1.0, QColor( 20,  60, 160, 100))
    painter.setBrush(QBrush(grad))
    painter.setPen(QPen(QColor(120, 180, 255, 180), 1))
    painter.drawEllipse(cx - R, cy_anim - R, R * 2, R * 2)

    # Núcleo
    r_c = max(3, R // 4)
    painter.setBrush(QBrush(QColor(255, 220, 120, 230)))
    painter.setPen(QPen(QColor(255, 180, 60, 200), 1))
    painter.drawEllipse(cx - r_c, cy_anim - r_c, r_c * 2, r_c * 2)

    if nombre:
        painter.setPen(QColor("#999999"))
        font = QFont(); font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(cx - len(nombre) * 5,
                         cy + int(MAX_OSC_PX) + R + 14, nombre)


# Alias usado por field_canvas
_dibujar_atomo_estatico = _dibujar_atomo_animado


class WaveCanvas(QWidget):
    """
    Canvas principal de ondas.
    No tiene timer propio — lee self.reloj.t en cada paintEvent.
    """

    def __init__(self, atomo, reloj, n_atomos=1):
        super().__init__()
        self.atomo      = atomo
        self.reloj      = reloj          # RelojGlobal compartido
        self.n_atomos   = n_atomos
        self.phase_kick = 0.8
        self.wave_mode  = "incidente_resultante"
        self.dx         = 50e-9

        reloj.suscribir(self)

    # ── Propiedades que delegan en el reloj ──────────────────
    @property
    def t(self):
        return self.reloj.t

    def start(self):
        self.reloj.start()

    def pause(self):
        self.reloj.pause()

    def set_n_atomos(self, n):
        self.n_atomos = max(1, int(n))
        self.update()

    def set_phase_kick(self, value):
        self.phase_kick = float(value)
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
        painter  = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width    = self.width()
        height   = self.height()
        centro_y = height // 2
        t        = self.reloj.t          # único punto de lectura del tiempo

        painter.fillRect(self.rect(), QColor("#101010"))
        painter.setPen(QPen(QColor("#404040"), 1))
        painter.drawLine(0, centro_y, width, centro_y)

        res = _en_resonancia(self.atomo)

        if self.wave_mode == "phase_kick":
            self._paint_phase_kick(painter, width, centro_y, t, res)
        elif self.wave_mode == "incidente_resultante":
            self._paint_multicapa(painter, width, centro_y, t, res)
        else:
            self._paint_modo_unico(painter, width, centro_y, t, res)

        self._paint_leyenda(painter, res)

    # ----------------------------------------------------------
    # Absorción
    # ----------------------------------------------------------

    def _paint_absorcion(self, painter, x_px, width, height):
        painter.fillRect(x_px, 0, width - x_px, height, QColor(180, 20, 20, 35))
        painter.setPen(QPen(QColor(255, 60, 60, 200), 2))
        painter.drawLine(x_px, 0, x_px, height)
        font = QFont(); font.setPointSize(12); font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 80, 80, 220))
        painter.drawText(x_px + 20, height // 2 - 10, "ABSORCIÓN  (ωr ≈ ωl)")
        font2 = QFont(); font2.setPointSize(9)
        painter.setFont(font2)
        painter.setPen(QColor(255, 140, 140, 180))
        painter.drawText(x_px + 20, height // 2 + 12,
                         "La onda no se propaga más allá del material")

    # ----------------------------------------------------------
    # phase_kick
    # ----------------------------------------------------------

    def _paint_phase_kick(self, painter, width, centro_y, t, res):
        atomos_px = self._posiciones_atomos_px(width)
        N         = len(atomos_px)
        bordes    = [0] + atomos_px + [width]
        n_seg     = 1 if res else N + 1

        delta_phi = phi_emision(self.atomo)
        for i in range(n_seg):
            painter.setPen(QPen(QColor("#ffdd00"), 2))
            for px in range(bordes[i], min(bordes[i + 1], width - 1)):
                x1 = px       * self.dx
                x2 = (px + 1) * self.dx
                y1 = centro_y + _onda_phase_kick(x1, t, i * delta_phi)
                y2 = centro_y + _onda_phase_kick(x2, t, i * delta_phi)
                painter.drawLine(px, int(y1), px + 1, int(y2))

        painter.setPen(QPen(QColor(100, 180, 255, 160), 1))
        for px in atomos_px:
            painter.drawLine(px, 0, px, self.height())

        radio = 8 if N > 5 else 14
        for px in atomos_px:
            _dibujar_atomo_animado(painter, px, centro_y, t, self.atomo, "", radio)

        if res:
            self._paint_absorcion(painter, atomos_px[0], width, self.height())

    # ----------------------------------------------------------
    # incidente_resultante
    # ----------------------------------------------------------

    def _paint_multicapa(self, painter, width, centro_y, t, res):
        atomos_px = self._posiciones_atomos_px(width)
        N         = len(atomos_px)
        C_inc = np.array([0x00, 0xff, 0x88])
        C_res = np.array([0xcf, 0xe9, 0x66])

        # ── Fasor acumulado: E0_eff recalculado en cada capa ──────
        # segmentos[i] = fasor complejo DESPUÉS de pasar por i átomos
        # El dibujo del segmento i usa abs(segmentos[i]) y phase(segmentos[i])
        E0_vis  = 50.0
        A_base  = _escalar_amplitud_con_atomo(amplitud_oscilacion(self.atomo), self.atomo)
        phi     = phi_emision(self.atomo)
        phasor  = complex(E0_vis, 0)
        segmentos = [phasor]
        for _ in range(N):
            A_i = A_base * (abs(phasor) / E0_vis)
            phasor += A_i * cmath.exp(1j * phi)
            segmentos.append(phasor)

        # ── Segmento 0: onda incidente pura ──────────────────────
        painter.setPen(QPen(QColor("#00ff88"), 2))
        for px in range(atomos_px[0]):
            x1 = px * self.dx; x2 = (px + 1) * self.dx
            y1 = centro_y + onda_incidente(x1, t)
            y2 = centro_y + onda_incidente(x2, t)
            painter.drawLine(px, int(y1), px + 1, int(y2))

        # ── Segmentos 1..N: resultante acumulada por capa ────────
        if not res:
            for i in range(N):
                px_start = atomos_px[i]
                px_end   = atomos_px[i + 1] if i + 1 < N else width
                amp      = abs(segmentos[i + 1])
                fase_seg = cmath.phase(segmentos[i + 1])
                alpha    = i / max(N - 1, 1)
                rgb      = ((1 - alpha) * C_inc + alpha * C_res).astype(int)
                painter.setPen(QPen(QColor(int(rgb[0]), int(rgb[1]), int(rgb[2])), 2))
                for px in range(px_start, min(px_end, width - 1)):
                    x1 = px * self.dx; x2 = (px + 1) * self.dx
                    y1 = centro_y + amp * np.sin(K_1 * x1 - OMEGA_L * t + fase_seg)
                    y2 = centro_y + amp * np.sin(K_1 * x2 - OMEGA_L * t + fase_seg)
                    painter.drawLine(px, int(y1), px + 1, int(y2))

        radio = 10 if N > 5 else 16
        for px in atomos_px:
            _dibujar_atomo_animado(painter, px, centro_y, t, self.atomo,
                                   "" if N > 1 else self.atomo.nombre, radio)

        painter.setPen(QPen(QColor(70, 70, 70, 90), 1))
        for px in atomos_px:
            painter.drawLine(px, 0, px, self.height())

        if res:
            self._paint_absorcion(painter, atomos_px[0], width, self.height())

    # ----------------------------------------------------------
    # Modos simples
    # ----------------------------------------------------------

    def _paint_modo_unico(self, painter, width, centro_y, t, res):
        atomo_cx = width // 2

        if self.wave_mode == "emitida":
            color   = QColor("#ffcc66")
            wave_fn = lambda x, t_: onda_emitida(abs(x), t_, self.atomo)
        elif self.wave_mode == "resultante":
            color   = QColor("#cfe966")
            wave_fn = lambda x, t_: onda_resultante(x, t_, self.atomo)
        else:
            color   = QColor("#00ff88")
            wave_fn = lambda x, t_: onda_incidente(x, t_)

        painter.setPen(QPen(color, 3))

        if res and self.wave_mode in ("resultante", "emitida"):
            _dibujar_atomo_animado(painter, atomo_cx, centro_y,
                                   t, self.atomo, self.atomo.nombre)
            self._paint_absorcion(painter, atomo_cx, width, self.height())
            return

        start_x = atomo_cx + 1 if self.wave_mode == "resultante" else 0
        end_x   = width        if self.wave_mode == "resultante" else width - 1
        if res and self.wave_mode == "incidente":
            end_x = atomo_cx

        for px in range(start_x, end_x):
            if self.wave_mode == "emitida":
                x1 = (px - atomo_cx) * self.dx
                x2 = (px + 1 - atomo_cx) * self.dx
            else:
                x1 = px * self.dx; x2 = (px + 1) * self.dx
            y1 = centro_y + wave_fn(x1, t)
            y2 = centro_y + wave_fn(x2, t)
            painter.drawLine(px, int(y1), px + 1, int(y2))

        _dibujar_atomo_animado(painter, atomo_cx, centro_y,
                               t, self.atomo, self.atomo.nombre)
        if res:
            self._paint_absorcion(painter, atomo_cx, width, self.height())

    # ----------------------------------------------------------
    # Leyenda
    # ----------------------------------------------------------

    def _paint_leyenda(self, painter, res):
        font = QFont(); font.setPointSize(9)
        painter.setFont(font)

        if res:
            painter.setPen(QColor("#00ff88"))
            painter.drawText(20, 20, "── Onda incidente")
            painter.setPen(QColor(255, 80, 80))
            painter.drawText(20, 38, "✕  Onda absorbida  (ωr = ωl)")
            return

        if self.wave_mode == "phase_kick":
            painter.setPen(QColor("#ffdd00"))
            painter.drawText(20, 20, "── Phase kick  (estilo 3B1B)")
            painter.setPen(QColor("#ff6666"))
            painter.drawText(20, 38, f"φ = {phi_emision(self.atomo):.3f} rad  (calculado de K)")
            painter.setPen(QColor("#aaaaaa"))
            painter.drawText(20, 56, f"N = {self.n_atomos} átomos")
        elif self.wave_mode == "incidente_resultante":
            painter.setPen(QColor("#00ff88"))
            painter.drawText(20, 20, "── Onda incidente")
            painter.setPen(QColor("#cfe966"))
            painter.drawText(20, 38, "── Onda resultante  (por segmento)")
            painter.setPen(QColor("#aaaaaa"))
            A_vis = _escalar_amplitud(amplitud_oscilacion(self.atomo))
            painter.drawText(20, 56, f"N = {self.n_atomos}  |  A_x = {A_vis:.1f} px")
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
            painter.drawText(20, 56,
                f"Átomo: {self.atomo.nombre}  |  A_x = {A_vis:.1f} px")