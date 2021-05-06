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

    def __init__(self):
        """Constructor (this code is run only once).

        The `self.` prefix indicates class properties. Such properties remain the
        same between separate calls to the `update()` method.
        """

        super().__init__()  # Keep this line

        # TODO: Initialize all the parameters for the musculoskeletal muscle
        #   Hints: Open a wrist model in Opensim and obtain the following relationships:
        #       - active and passive force-length,  angle-length and angle-moment arm
        #       - maximal isometric force and pennation angle for each muscle (flexor and extensor)

        self.emg_scale = 1.0  # Example of a property in Python

    def update(self, angle: float, emg1: float, emg2: float) -> float:
        """Compute the next step in the muscle_model.

        :param angle: The current angle of the wrist
        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Torque [Nm]
        """

        # TODO: Enter custom neural muscular model here

        # Simply take EMG as proportional to torque
        return (emg1 - emg2) / self.emg_scale


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

        Note: don't use the same filter object for more than one signal! The filter
        object contains the filter state, which should be unique per signal.
        """

        # TODO: Add your own filters and other parameters here

        # Create 4th order low-pass filter with a cut-off frequency of 5 Hz
        # Compute Butterworth coefficients and pass them into a filter object
        lowpass_wc = 5.0 / (0.5 * self.FS)
        lowpass_b, lowpass_a = signal.butter(4, lowpass_wc, btype='low')

        self.lowpass_filter_1 = DigitalFilter(lowpass_b, lowpass_a)
        self.lowpass_filter_2 = DigitalFilter(lowpass_b, lowpass_a)

    def update(self, emg1: float, emg2: float) -> (float, float):
        """Filter EMG signal.

        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Both filtered values
        """

        # TODO: Replace with custom EMG filtering

        # Apply lowpass filter to emg1
        emg1_filtered = self.lowpass_filter_1.sample(emg1)
        emg2_filtered = self.lowpass_filter_2.sample(emg2)

        return emg1_filtered, emg2_filtered
