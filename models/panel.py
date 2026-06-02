from PyQt6.QtWidgets import QFrame


class Panel(QFrame):

    def __init__(self, name=""):

        super().__init__()

        self.setFrameShape(
            QFrame.Shape.Box
        )

        self.setLineWidth(2)

        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px solid #4a4a4a;
                border-radius: 5px;
            }
        """)
   