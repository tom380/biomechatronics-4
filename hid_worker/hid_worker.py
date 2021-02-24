from PyQt5.QtCore import QObject, pyqtSignal
import ctypes
import struct
import hid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class HIDWorker(QObject):
    """"Worker object to run in it's own thread to listen to HID reports."""

    HID_REPORT_SIZE = 64

    # Signal that's fired with a new block of data
    update = pyqtSignal(int, list)

    def __init__(self, device: hid.device):
        """Constructor."""
        super().__init__()

        self.device = device

        self._is_running = True

    def run(self):
        """Thread function.

        The read that is being performed is non-blocking (configured in device
        creation). This keeps the thread responsive to the stop flag.
        """

        self._is_running = True

        while self._is_running:
            d = self.device.read(self.HID_REPORT_SIZE)
            if not d:
                continue  # Empty data

            channels = d[0]

            number_bytes = ctypes.sizeof(ctypes.c_long) + channels * ctypes.sizeof(
                ctypes.c_float)

            mask = 'L' + (channels * 'f')
            frame = struct.unpack(mask, bytearray(d[1:(1 + number_bytes)]))
            micros = frame[0]
            new_data = list(frame[1:])

            # self.window.update_data(list(new_data))

            self.update.emit(micros, new_data)

    def stop(self):
        """Stop the main loop of this worker."""
        self._is_running = False
