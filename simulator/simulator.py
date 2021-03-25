from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QPaintEvent, QPixmap, QColor, QPen
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
        self.w = 1100
        self.h = 700
        self.setFixedSize(self.w, self.h)

        self._angle = 0.0  # Angle of the wrist
        self._target = 0.0  # Target angle

        # .svg images are exported at 60 dpi - The bitmaps are not rescaled in Python
        # for the best quality
        self.image_hand = QPixmap('images/hand_hand.png')
        self.image_wrist = QPixmap('images/hand_wrist.png')
        self.image_dial = QPixmap('images/dial.png')

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

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def paintEvent(self, event: QPaintEvent) -> None:
        """Callback for when the visuals of the frame are updated."""

        painter = QPainter(self)

        dial_x = int((self.w - self.image_dial.width()) / 2 - 10)
        dial_y = self.h - self.image_dial.height() - self.image_wrist.height() + 20
        painter.drawPixmap(dial_x, dial_y, self.image_dial)

        wrist_x = int((self.w - self.image_wrist.width()) / 2)
        wrist_y = self.h - self.image_wrist.height()
        painter.drawPixmap(wrist_x, wrist_y, self.image_wrist)

        # The rotated hand needs better rendering options
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Move painter to the point of rotation (tip of the wrist)
        pivot_x = int(self.w / 2) - 10
        pivot_y = wrist_y + 10
        painter.translate(pivot_x, pivot_y)

        painter.rotate(self._angle)

        # painter.drawPixmap(-30, -70, self.image_hand)
        # Now move the bottom of the hand to the pivot point:
        painter.drawPixmap(-int(self.image_hand.width() / 2) + 20,
                           -self.image_hand.height() + 20,
                           self.image_hand)

        # Draw reticle indicating current angle
        painter.setBrush(QColor('#00c1ff'))

        reticle_radius = -int(self.image_dial.width() * 0.5) + 88
        painter.drawEllipse(0 - 8, reticle_radius - 8, 16, 16)

        # Create new painter to draw the target reticle
        painter_target = QPainter(self)

        painter_target.translate(pivot_x, pivot_y)
        painter_target.rotate(self._target)

        pen = QPen()
        pen.setWidth(5)
        pen.setColor(QColor(200, 0, 0))
        painter_target.setPen(pen)
        painter_target.drawEllipse(0 - 13, reticle_radius - 13, 26, 26)
