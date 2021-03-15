from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QPaintEvent, QPixmap
from PyQt5.QtCore import QTimer


class Simulator(QFrame):
    """Window to display hand simulation.

    The frame updates itself with an internal timer. Simply change the `angle`
    property to change the visualization.
    """

    FPS = 120.0  # Twice the monitor refresh rate gives the quickest result

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.setStyleSheet('QFrame { background: none; }')
        self.setFixedSize(600, 600)

        self._angle = 0.0  # Angle of the wrist

        # .svg images are exported at 60 dpi - The bitmaps are not rescaled in Python
        # for the best quality
        self.image_hand = QPixmap('images/hand_hand.png')
        self.image_wrist = QPixmap('images/hand_wrist.png')

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(int(1000.0 / self.FPS))

    @property
    def angle(self):
        """Get wrist angle."""
        return self._angle

    @angle.setter
    def angle(self, value: float):
        """Update the wrist angle."""
        self._angle = value

    def paintEvent(self, event: QPaintEvent) -> None:
        """Callback for when the visuals of the frame are updated."""

        painter = QPainter(self)

        painter.drawPixmap(0, 300, self.image_wrist)

        # The rotated hand needs better rendering options
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        painter.translate(170, 350)

        painter.rotate(self._angle)

        painter.drawPixmap(-30, -70, self.image_hand)
