from enum import Enum
import struct


class Mode(Enum):
    HEADER = 1
    SIZE = 2
    TIME = 3
    DATA = 4


class PlotDecoder:
    """Class to decode the BioRobotics plot protocol.

    The serial protocol is as follows:

    First the header (3 bytes): 7f ff bf
    Then the channel count (1 byte): 03
    Then the microtime (4 bytes, signed integer): 00 01 01 01
    Then follow the floats (4 bytes each): 01 01 01 01 ...
    """

    def __init__(self, *args, **kwargs):
        """Constructor."""

        self.header_bytes = [b'\x7f', b'\xff', b'\xbf']
        self.buffer = bytearray()  # Store bytes while receiving
        self.mode = Mode.HEADER
        self.bytes_count = 0  # Number of bytes in current mode

        self.channel_size = 0  # Number of channels
        self.time = 0  # Read microtime
        self.data = []  # Received floats

    def set_state(self, new_mode: Mode):
        """Simple wrapper to change mode."""

        self.mode = new_mode
        self.bytes_count = 0
        self.buffer = bytearray()

        if new_mode == Mode.DATA:
            self.data = []

    def receive_byte(self, byte: bytearray) -> bool:
        """Precess new incoming byte.

        Return true when a complete package was received
        """

        if self.mode == Mode.HEADER:  # If header not passed

            # Increment header
            if byte == self.header_bytes[self.bytes_count]:
                self.bytes_count += 1
            else:
                self.bytes_count = 0  # Reset, header failed

            if self.bytes_count >= 3:  # Header completed
                self.set_state(Mode.SIZE)

            return False

        if self.mode == Mode.SIZE:
            self.channel_size = int.from_bytes(byte, byteorder='big', signed=False)
            self.set_state(Mode.TIME)

            return False

        if self.mode == Mode.TIME:
            self.buffer.append(byte[0])

            if len(self.buffer) == 4:
                # print(''.join('{:02x}'.format(x) for x in self.buffer))

                self.time = int.from_bytes(self.buffer, byteorder='big', signed=True)
                self.set_state(Mode.DATA)

            return False

        if self.mode == Mode.DATA:
            self.buffer.append(byte[0])

            if len(self.buffer) == 4:
                value = struct.unpack('f', self.buffer)
                self.buffer = bytearray()
                self.data.append(value)

            if len(self.data) == self.channel_size:
                self.set_state(Mode.HEADER)
                return True

            return False

        return False
