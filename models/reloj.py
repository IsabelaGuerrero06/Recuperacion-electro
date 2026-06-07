"""
reloj.py — Reloj global compartido por todos los canvas.

Un único QTimer avanza `t` y notifica a todos los suscriptores
para que se repinten. Esto garantiza que wave_canvas, field_canvas
y sidebar usen exactamente el mismo instante de tiempo en cada frame.
"""

from PyQt6.QtCore import QTimer


class RelojGlobal:

    def __init__(self, dt=1e-18, time_scale=200.0, fps=16):
        self.t          = 0.0
        self.dt         = dt
        self.time_scale = time_scale
        self._suscriptores = []   # lista de widgets que llaman a update()

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(fps)
        self.is_running = True

    def suscribir(self, widget):
        """Registra un widget para que se repinte en cada tick."""
        if widget not in self._suscriptores:
            self._suscriptores.append(widget)

    def _tick(self):
        self.t += self.dt * self.time_scale
        for w in self._suscriptores:
            w.update()

    def start(self):
        if not self.timer.isActive():
            self.timer.start(16)
        self.is_running = True

    def pause(self):
        self.timer.stop()
        self.is_running = False