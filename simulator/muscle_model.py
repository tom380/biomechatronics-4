class MuscleModel:
    """Base class for the EMG-steered neural-muscular muscle_model.

    The muscle_model will take in unfiltered EMG and will output a torque that is applied to
    the hand.

    Override the `update()` method to insert your own muscle_model.
    """

    FS = 750.0  # EMG sampling rate

    def update(self, emg1: float, emg2: float) -> float:
        """Compute the next step in the muscle_model.

        Note: peak wrist torque is in the order of +/- 10 Nm

        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Torque [Nm]
        """
        # Simply take EMG as proportional to torque
        return (emg1 - emg2) * 10.0
