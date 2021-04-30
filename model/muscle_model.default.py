from scipy import signal

from simulator.muscle_model_base import MuscleModelBase, EmgFilterBase
from simulator.digital_filter import DigitalFilter


class MuscleModel(MuscleModelBase):
    """Class for the EMG-steered neural-muscular muscle_model.

    The muscle model will take in unfiltered EMG and will output a torque that is
    applied to the hand.

    Extend the `update()` method to insert your own muscle_model.

    Use `self.FS` for the sample frequency.
    """

    def update(self, emg1: float, emg2: float) -> float:
        """Compute the next step in the muscle_model.

        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Torque [Nm]
        """

        # TODO: Enter custom neural muscular model here

        # Simply take EMG as proportional to torque
        return emg1 - emg2


class EmgFilter(EmgFilterBase):
    """Class for filtering the EMG signals.

    This class will filter the incoming EMG signals. The output of `update`
    will be directly send to `MuscleModel.update(...)`.

    The `update()` method will perform the actual filtering. Use the `__init__()`
    method for code that needs to be run only once (e.g. to create any filter
    objects).

    The filtered output is shown in the graphs of the application.
    """

    def __init__(self):
        """Constructor (this code is run only once).

        The `self.` prefix indicates class properties. Such properties remain the
        same between separate calls to the `update()` method.
        """

        # TODO: Add your own filters and other parameters here

        # Create 4th order low-pass filter with a cut-off frequency of 5 Hz
        # Compute Butterworth coefficients and pass them into a filter object
        lowpass_wc = 5.0 / (0.5 * self.FS)
        lowpass_b, lowpass_a = signal.butter(4, lowpass_wc, btype='low')

        self.lowpass_filter = DigitalFilter(lowpass_b, lowpass_a)

    def update(self, emg1: float, emg2: float) -> (float, float):
        """Filter EMG signal.

        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Both filtered values
        """

        # TODO: Replace with custom EMG filtering

        # Apply lowpass filter to emg1
        emg1_filtered = self.lowpass_filter.sample(emg1)
        emg2_filtered = emg2

        return emg1_filtered, emg2_filtered
