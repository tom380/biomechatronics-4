from scipy.interpolate import CubicSpline, splprep


class MuscleModelBase:
    """Base class for the EMG-steered neural-muscular muscle_model.

    The muscle_model will take in filtered EMG and will output a torque that is applied to
    the hand.

    Override the `update()` method to insert your own muscle_model.
    """

    FS = 750.0  # EMG sampling rate

    def update(self, angle: float, emg1: float, emg2: float) -> float:
        """Compute the next step in the muscle_model.

        Note: peak wrist torque is in the order of +/- 10 Nm

        :param angle: The current angle of the wrist
        :param emg1: Filtered EMG (channel 0)
        :param emg2: Filtered EMG (channel 1)
        :return: Torque [Nm]
        """

        # Extend this class and override this method to add your own model
        return 0.0


class EmgFilterBase:
    """Base class for the EMG filtering.

    The `update()` method will take in unfiltered EMG and should output filtered values.
    Extend this class to and override the `update()` method add your own code.
    The filtered result will be passed on to `MuscleModel`.
    """

    FS = MuscleModelBase.FS

    def update(self, emg1: float, emg2: float) -> (float, float):
        """Filter EMG input.

        By default no filtering is done at all.

        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Both filtered values
        """
        return emg1, emg2
