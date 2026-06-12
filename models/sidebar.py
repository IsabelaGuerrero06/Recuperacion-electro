import cmath
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
    phi_emision_real,
)

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QRadialGradient, QFont
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QLabel, QScrollArea,
    QComboBox,
)

from models.panel import Panel


class CalculationSidebar(Panel):
    """
    Panel inferior derecho.
    Muestra cálculos del modelo de Lorentz + animación del electrón.
    El electrón animado SOLO existe aquí.
    """

    def __init__(self, wave_canvas, atomo, on_wave_mode_change=None):
        super().__init__()

        self.wave_canvas = wave_canvas
        self.atomo       = atomo
        self.on_wave_mode_change = on_wave_mode_change
        self.wave_mode = "incidente_resultante"
        self.n_atomos  = 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Modelo de Lorentz — Cálculos")
        title.setStyleSheet(
            "color: #ffffff; font-weight: bold; font-size: 13px;"
        )
        layout.addWidget(title)

        selector_label = QLabel("Tipo de onda")
        selector_label.setStyleSheet("color: #cfcfcf; font-size: 11px;")
        layout.addWidget(selector_label)

        self.wave_selector = QComboBox()
        self.wave_selector.addItem("Incidente + resultante", "incidente_resultante")
        self.wave_selector.addItem("Emitida (átomo)", "emitida")
        self.wave_selector.addItem("Solo resultante", "resultante")
        self.wave_selector.addItem("Solo incidente", "incidente")
        self.wave_selector.addItem("Phase kick", "phase_kick")
        self.wave_selector.currentIndexChanged.connect(self._on_wave_change)
        layout.addWidget(self.wave_selector)

        # ── Widget animado (solo aquí) ────────────────────────
        self.electron_anim = ElectronAnimation(atomo)
        self.electron_anim.setFixedHeight(90)
        layout.addWidget(self.electron_anim)

        # ── Texto de cálculos ─────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        self.lorentz_label   = QLabel()
        self.onda_label      = QLabel()
        self.campo_e_label   = QLabel()
        self.campo_b_label   = QLabel()
        self.multicapa_label = QLabel()

        for label in [
            self.lorentz_label,
            self.onda_label,
            self.campo_e_label,
            self.campo_b_label,
            self.multicapa_label,
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
        content_layout.addWidget(self.multicapa_label)
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

    def set_k(self, valor_k):
        """Actualiza la constante elástica del átomo (N/m)."""
        self.atomo.set_k(valor_k)
        self.update_values()

    def set_n_atomos(self, n):
        """Actualiza N capas y refresca los cálculos."""
        self.n_atomos = max(1, int(n))
        self.update_values()

    def set_phase_kick(self, value):
        """Placeholder para compatibilidad con otros canvas."""
        pass

    def _fmt(self, value):
        return f"{value:.3e}"

    def _on_wave_change(self):
        mode = self.wave_selector.currentData()
        if mode:
            self.wave_mode = mode
            if self.on_wave_mode_change is not None:
                self.on_wave_mode_change(mode)
            self.update_values()

    def _calcular_segmentos(self):
        """
        Propaga la onda a través de self.n_atomos capas.

        El ratio de emisión se calcula de forma adimensional:

            A_ref = q·E0 / (m·ωl²)    →  la amplitud que tendría el electrón
                                           si ωr = 0 (límite estático)
            A_fis = q·E0 / (m·(ωr²−ωl²))

            ratio = A_fis / A_ref = ωl² / (ωr² − ωl²)

        Así ratio es puro número: cuánto emite el átomo por unidad de campo
        normalizado que recibe. El fasor se propaga normalizado a 1 (= E0).

        φ = phi_emision_real(atomo) = −arctan(γ·ωl / (ωr²−ωl²))
        """
        a    = self.atomo
        A_fis = amplitud_oscilacion_real(a)           # metros reales
        A_ref = (a.q * 50.0) / (a.m * OMEGA_1**2)    # amplitud de referencia (m)
        ratio = A_fis / A_ref if abs(A_ref) > 1e-60 else 0.0   # adimensional
        phi   = phi_emision_real(a)

        phasor    = complex(1.0, 0)   # normalizado: phasor_0 = 1 × E0
        segmentos = [phasor]

        for _ in range(self.n_atomos):
            A_emit = ratio * abs(phasor)
            phasor = phasor + A_emit * cmath.exp(1j * phi)
            if abs(phasor) > 1e4:
                phasor = 1e4 * phasor / abs(phasor)
            segmentos.append(phasor)

        return segmentos, phi, ratio

    def _texto_multicapa(self):
        """Genera las líneas HTML para la sección de N capas."""
        N = self.n_atomos

        # Solo mostrar si está en el modo correcto o si N > 1
        if self.wave_mode not in ("incidente_resultante",) and N == 1:
            self.multicapa_label.setText("")
            return

        segmentos, phi, ratio = self._calcular_segmentos()
        phi_deg = np.degrees(phi)

        lineas = [
            "<span style='color:#ff9966;font-weight:bold;'>Propagación N capas</span>",
            "─────────────────────────────────────",
            f"  N = {N} capas",
            f"  φ_emisión = {phi:.4f} rad  ({phi_deg:.2f}°)",
            f"  ratio = ωl²/(ωr²−ωl²) = {ratio:.4f}",
            "",
            "  <span style='color:#aaaaaa;'>Fasor (normalizado a E0):</span>",
            "  p[i] = p[i-1] + ratio·|p[i-1]|·e^(iφ)",
            "",
        ]

        # Mostrar las primeras capas, la del medio (si N>6) y la última
        MAX_SHOW = 5
        if N <= MAX_SHOW * 2:
            indices = list(range(N + 1))
        else:
            # primeras MAX_SHOW, «…», última
            indices = list(range(MAX_SHOW)) + [-1] + [N]

        prev_ellipsis = False
        for idx in indices:
            if idx == -1:
                lineas.append("  &nbsp;&nbsp;⋮")
                prev_ellipsis = True
                continue
            p   = segmentos[idx]
            amp = abs(p)
            fase = cmath.phase(p)
            fase_deg = np.degrees(fase)
            if idx == 0:
                etiqueta = "incidente"
                color    = "#00ff88"
            elif idx == N:
                etiqueta = "final "
                color    = "#cfe966"
            else:
                etiqueta = f"capa {idx:2d}"
                color    = "#aaccff"
            lineas.append(
                f"  <span style='color:{color};'>p[{idx:3d}]</span>"
                f"  amp={amp:.4f}  φ={fase_deg:+7.2f}°  ({etiqueta})"
            )

        # Resumen final
        p_final   = segmentos[N]
        amp_final = abs(p_final)
        fase_final = np.degrees(cmath.phase(p_final))
        delta_fase = fase_final  # respecto a la incidente (fase_0 = 0°)

        lineas += [
            "",
            "  <span style='color:#ffd166;'>Resumen tras N capas:</span>",
            f"  Amplitud resultante = {amp_final:.4f} × E0",
            f"  Desfase acumulado   = {delta_fase:+.2f}°",
        ]

        # Indicar régimen físico
        if abs(phi_deg + 90) < 5:
            regimen = "resonancia — absorción máxima"
            col_reg = "#ff5555"
        elif phi_deg > -90:
            regimen = "sub-resonante — adelanto de fase"
            col_reg = "#88ddff"
        else:
            regimen = "super-resonante — retraso de fase"
            col_reg = "#ffaa55"
        lineas.append(
            f"  <span style='color:{col_reg};'>Régimen: {regimen}</span>"
        )

        self.multicapa_label.setText("<br>".join(lineas))

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

        if self.wave_mode == "incidente_resultante":
            ondas_lineas = [
                "f(x,t) = A1·sin(k·x − ωl·t)",
                f"  f = {self._fmt(f_inc)}",
                "g(x,t) = A_x·sin(k·x − ωl·t + φ)",
                f"  g = {self._fmt(f_emit)}",
                "r = f + g",
                f"  r = {self._fmt(f_res)}",
            ]
        elif self.wave_mode == "emitida":
            ondas_lineas = [
                "g(x,t) = A_x·sin(k·x − ωl·t + φ)",
                f"  g = {self._fmt(f_emit)}",
            ]
        elif self.wave_mode == "resultante":
            ondas_lineas = [
                "r = f + g",
                f"  r = {self._fmt(f_res)}",
            ]
        else:
            ondas_lineas = [
                "f(x,t) = A1·sin(k·x − ωl·t)",
                f"  f = {self._fmt(f_inc)}",
            ]

        self.onda_label.setText("<br>".join([
            "<span style='color:#00ff88;font-weight:bold;'>Ondas</span>",
            "─────────────────────────────────────",
            *ondas_lineas,
        ]))

        if self.wave_mode == "incidente_resultante":
            e_lineas = [
                "E_inc  = E0·cos(k·x − ωl·t)",
                f"  E_inc  = {self._fmt(E_inc)} V/m",
                "E_emit = A_x·cos(k·x − ωl·t + φ)",
                f"  E_emit = {self._fmt(E_emit)} V/m",
                f"  E_res  = {self._fmt(E_res)} V/m",
            ]
        elif self.wave_mode == "emitida":
            e_lineas = [
                "E_emit = A_x·cos(k·x − ωl·t + φ)",
                f"  E_emit = {self._fmt(E_emit)} V/m",
            ]
        elif self.wave_mode == "resultante":
            e_lineas = [
                "E_res = E_inc + E_emit",
                f"  E_res = {self._fmt(E_res)} V/m",
            ]
        else:
            e_lineas = [
                "E_inc = E0·cos(k·x − ωl·t)",
                f"  E_inc = {self._fmt(E_inc)} V/m",
            ]

        self.campo_e_label.setText("<br>".join([
            "<span style='color:#7ad1ff;font-weight:bold;'>Campo Eléctrico</span>",
            "─────────────────────────────────────",
            *e_lineas,
        ]))

        B0 = 50 / C
        if self.wave_mode == "incidente_resultante":
            b_lineas = [
                "B_inc  = (E0/c)·cos(k·x − ωl·t)",
                f"  B0 = {self._fmt(B0)} T",
                f"  B_inc  = {self._fmt(B_inc)} T",
                f"  B_emit = {self._fmt(B_emit)} T",
                f"  B_res  = {self._fmt(B_res)} T",
            ]
        elif self.wave_mode == "emitida":
            b_lineas = [
                "B_emit = (A_x/c)·cos(k·x − ωl·t + φ)",
                f"  B_emit = {self._fmt(B_emit)} T",
            ]
        elif self.wave_mode == "resultante":
            b_lineas = [
                "B_res = B_inc + B_emit",
                f"  B_res = {self._fmt(B_res)} T",
            ]
        else:
            b_lineas = [
                "B_inc = (E0/c)·cos(k·x − ωl·t)",
                f"  B0 = {self._fmt(B0)} T",
                f"  B_inc = {self._fmt(B_inc)} T",
            ]

        self.campo_b_label.setText("<br>".join([
            "<span style='color:#ff7aa2;font-weight:bold;'>Campo Magnético</span>",
            "─────────────────────────────────────",
            *b_lineas,
        ]))

        # ── Sección N capas ───────────────────────────────────
        self._texto_multicapa()


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