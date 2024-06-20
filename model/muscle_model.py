from scipy import signal
from scipy.interpolate import CubicSpline
from scipy.interpolate import PchipInterpolator

from simulator.muscle_model_base import MuscleModelBase, EmgFilterBase
from simulator.digital_filter import DigitalFilter

import numpy as np

class Muscle:
    def __init__(self):
        self.optimal_fibre_length = None
        self.max_isometric_force = None
        self.pennation_angle_at_optimal = None
        self.tendon_slack_length = None
        self.active_fl = None
        self.passive_fl = None
        self.muscle_tendon_length = None
        self.flexion_moment_arm = None

class ForceLengthRelationship:
    def __init__(self):
        self.x = []
        self.y = []

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

        # Create an instance of Muscle
        FCR = Muscle()
        ECRL = Muscle()

        # Define muscle properties
        FCR.optimal_fibre_length = 0.0628
        FCR.max_isometric_force = 59.7
        FCR.pennation_angle_at_optimal = 0.05410521
        FCR.tendon_slack_length = 0.2185

        ECRL.optimal_fibre_length = 0.0936
        ECRL.max_isometric_force = 65.7
        ECRL.pennation_angle_at_optimal = 0.04363323
        ECRL.tendon_slack_length = 0.2026

        # Define active and passive force-length relationships
        active_fl = ForceLengthRelationship()
        active_fl.x = [-35, 0, 0.401, 0.402, 0.4035, 0.52725, 0.62875, 0.71875, 0.86125, 1.045, 1.2175, 1.43875, 1.61875, 1.62, 1.621, 2.2, 35]
        active_fl.y = [0, 0, 0, 0, 0, 0.226667, 0.636667, 0.856667, 0.95, 0.993333, 0.77, 0.246667, 0, 0, 0, 0, 0]

        passive_fl = ForceLengthRelationship()
        passive_fl.x = [-35, 0.998, 0.999, 1.15, 1.25, 1.35, 1.45, 1.55, 1.65, 1.75, 1.7501, 1.7502, 35]
        passive_fl.y = [0, 0, 0, 0, 0.035, 0.12, 0.26, 0.55, 1.17, 2, 2, 2, 2]

        # Compute the splines using CubicSpline
        active_fl_spline = PchipInterpolator(active_fl.x, active_fl.y)
        passive_fl_spline = PchipInterpolator(passive_fl.x, passive_fl.y)

        FCR.active_fl = active_fl_spline
        FCR.passive_fl = passive_fl_spline
        ECRL.active_fl = active_fl_spline
        ECRL.passive_fl = passive_fl_spline

        angle = [-0.99959767, -0.75278343, -0.50596919, -0.25915495, -0.01234071, 0.23447353, 0.48128776, 0.72810200, 0.97491624, 1.22173048]
        muscle_tendon_length_ECRL = [ 0.29104195, 0.29376832, 0.29648413, 0.29914435, 0.30170628, 0.30412959, 0.30637666, 0.30841293, 0.31020735, 0.31173271]
        muscle_tendon_length_FCR = [0.29935362, 0.29641423, 0.29315810, 0.28963728, 0.28590906, 0.28203596, 0.27808623, 0.27413594, 0.27027482, 0.26662228]
        flexion_moment_arm_ECRL = [-0.01100436, -0.01105605, -0.01092046, -0.01060718, -0.01012554, -0.00948575, -0.00869947, -0.00777998, -0.00674223, -0.00560273]
        flexion_moment_arm_FCR = [0.01120295, 0.01258428, 0.01376582, 0.01472566, 0.01544287, 0.01589591, 0.01605878, 0.01589178, 0.01531788, 0.01415557]
        ECRL.muscle_tendon_length = PchipInterpolator(angle, muscle_tendon_length_ECRL)
        FCR.muscle_tendon_length = PchipInterpolator(angle, muscle_tendon_length_FCR)
        ECRL.flexion_moment_arm = PchipInterpolator(angle, flexion_moment_arm_ECRL)
        FCR.flexion_moment_arm = PchipInterpolator(angle, flexion_moment_arm_FCR)

        self.FCR = FCR
        self.ECRL = ECRL
        self.emg_scale = 1.0  # Example of a property in Python

    def update(self, angle: float, emg1: float, emg2: float) -> float:
        """Compute the next step in the muscle_model.

        :param angle: The current angle of the wrist
        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Torque [Nm]
        """

        ECRL = self.ECRL
        FCR = self.FCR

        ECRL_activation = self.muscle_activation(emg1, -0.001)
        FCR_activation = self.muscle_activation(emg2, -0.002)

        ECRL_force = self.muscle_tendon_force(ECRL, ECRL_activation, angle)
        FCR_force = self.muscle_tendon_force(FCR, FCR_activation, angle)

        torque = ECRL_force * ECRL.flexion_moment_arm(angle) + FCR_force * FCR.flexion_moment_arm(angle)

        # Simply take EMG as proportional to torque
        # return (emg1 - emg2) / self.emg_scale
        return torque
    
    def muscle_activation(self, u, A):
        return (np.exp(A * u / 1) - 1) / (np.exp(A) - 1)

    def muscle_tendon_force(self, muscle: Muscle, activation, angle):
        lt = muscle.tendon_slack_length
        lo = muscle.optimal_fibre_length
        phi_o = muscle.pennation_angle_at_optimal
        lmt = muscle.muscle_tendon_length(angle)
        lm = np.sqrt((lo * np.sin(phi_o)) ** 2 + (lmt - lt) ** 2)

        fA = muscle.active_fl
        fP = muscle.passive_fl
        Fmax = muscle.max_isometric_force
        FA = fA(lm/lo) * Fmax * activation
        FP = fP(lm/lo) * Fmax
        Fm = FA + FP

        phi = np.arcsin((lo * np.sin(phi_o)) / lm)
        Fmt = Fm * np.cos(phi)

        return Fmt


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

        self.MVC1 = 0.18
        self.MVC2 = 0.065

        fnotch = 50
        Qnotch = 2
        notch_b, notch_a = signal.iirnotch(fnotch, Qnotch, self.FS)

        fhighpass = 15
        highpass_wc = fhighpass / (self.FS / 2)
        highpass_b, highpass_a = signal.butter(2, highpass_wc, btype='high')

        flowpass = 1.6
        lowpass_wc = flowpass / (self.FS / 2)
        lowpass_b, lowpass_a = signal.butter(2, lowpass_wc, btype='low')

        self.notch_filter1 = DigitalFilter(notch_b, notch_a)
        self.highpass_filter1 = DigitalFilter(highpass_b, highpass_a)
        self.lowpass_filter1 = DigitalFilter(lowpass_b, lowpass_a)
        self.notch_filter2 = DigitalFilter(notch_b, notch_a)
        self.highpass_filter2 = DigitalFilter(highpass_b, highpass_a)
        self.lowpass_filter2 = DigitalFilter(lowpass_b, lowpass_a)

    def update(self, emg1: float, emg2: float) -> (float, float):
        """Filter EMG signal.

        :param emg1: Unfiltered EMG (channel 0)
        :param emg2: Unfiltered EMG (channel 1)
        :return: Both filtered values
        """

        emg1_filtered = self.lowpass_filter1.sample(np.abs(self.highpass_filter1.sample(self.notch_filter1.sample(emg1)))) / self.MVC1
        emg2_filtered = self.lowpass_filter2.sample(np.abs(self.highpass_filter2.sample(self.notch_filter2.sample(emg2)))) / self.MVC2

        return emg1_filtered, emg2_filtered
