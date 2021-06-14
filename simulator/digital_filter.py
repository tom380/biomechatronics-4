from scipy import signal
import numpy as np


class DigitalFilter:
    """Implementation of digital FIR filter, based on scipy.signal.

    scipy has many filter functions, but not a clean object for real-time filtering.
    This classes wraps around a little cheat to use the scipy filter functions.

    Important: use only a single filter instance per signal! The filter state is
    stored inside the object.
    """

    def __init__(self, b: list, a: list):
        """
        Use a scipy.signal function to compute your desired filter coefficients.

        :param b: Numerator coefficients
        :param a: Denominator coefficients
        """

        self.b = b
        self.a = a

        # Compute filter state corresponding to steady-state after a unit step response
        self.z = signal.lfilter_zi(self.b, self.a)

        self.z *= 0  # Force back to zero, filter is steadied for input = 0
        # We overwrite the values but the right array size is kept

    def sample(self, x: float) -> float:
        """Filter one more sample.

        :param x: New value (scalar)
        :return: Filtered value
        """

        y, self.z = signal.lfilter(self.b, self.a, [x], zi=self.z)
        # Output could be an array, convert to scalar

        if isinstance(y, np.ndarray):
            return y[0]
        return float(y)
