from simulator.muscle_model_base import MuscleModelBase


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
