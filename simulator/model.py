class Model:
    """Base class for the EMG-hand model."""

    FS = 750.0  # EMG sampling rate

    def __init__(self):
        self.angle = 0

    def update(self, emg1: float, emg2: float) -> float:
        self.angle += (emg1 - emg2) / self.FS * 100.0

        if self.angle > 90.0:
            self.angle = 90.0
        elif self.angle < -90.0:
            self.angle = -90.0

        return self.angle
