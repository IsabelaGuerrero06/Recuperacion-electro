from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class FieldCanvas(QWidget):

    def __init__(
        self,
        material,
        incidente_func,
        resultante_func,
        color,
        titulo
    ):
        super().__init__()

        self.material = material

        self.incidente_func = incidente_func
        self.resultante_func = resultante_func

        self.color = QColor(color)

        self.titulo = titulo

        self.dx = 50e-9
        self.dt = 1e-18
        self.time_scale = 200

        self.t = 0

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_simulation
        )

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

        # eje

        painter.setPen(
            QPen(QColor("#404040"), 1)
        )

        painter.drawLine(
            0,
            centro_y,
            width,
            centro_y
        )

        # material

        material_x = width // 2

        painter.fillRect(
            material_x - 30,
            20,
            60,
            height - 40,
            QColor(200, 200, 200, 80)
        )

        # titulo

        painter.setPen(QColor("white"))

        painter.drawText(
            10,
            20,
            self.titulo
        )

        # incidente

        painter.setPen(
            QPen(self.color, 3)
        )

        for x in range(material_x):

            x1 = x * self.dx
            x2 = (x + 1) * self.dx

            y1 = centro_y + self.incidente_func(
                x1,
                self.t
            )

            y2 = centro_y + self.incidente_func(
                x2,
                self.t
            )

            painter.drawLine(
                x,
                int(y1),
                x + 1,
                int(y2)
            )

        # resultante

        for x in range(material_x, width):

            x1 = x * self.dx
            x2 = (x + 1) * self.dx

            y1 = centro_y + self.resultante_func(
                x1,
                self.t,
                self.material
            )

            y2 = centro_y + self.resultante_func(
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