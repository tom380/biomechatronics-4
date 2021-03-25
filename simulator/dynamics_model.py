class DynamicsModel:
    """Model of the dynamics of the hand.

    This muscle_model should not be overridden by students.

    The muscle_model is integrated with simple Euler on each `update()`.

    A positive angle means flexion (the palm is lowered, towards the elbow).
    """

    def __init__(self, dt: float):
        """

        :param dt: Model time step
        """
        self._angle = 0
        self._velocity = 0
        self._dt = dt

        # Consider the hand as a rod of equally distributed mass
        # Not a great assumption, but the order of magnitude should be okay
        self.mass = 0.6  # [kg], from: https://exrx.net/Kinesiology/Segments
        self.length = 0.10  # [m], 0.19m from:
        # https://www.researchgate.net/figure/Measurements-cm-of-hand-length-in-males-and-females_tbl1_257737146
        # but we reduce it a bit because the center of mass will be close to the wrist

        self.inertia = 1.0 / 3.0 * self.mass * pow(self.length, 2)  # [kg m^2]

        self.damping = 0.03  # Found entirely by trial and error, such that motion
        # damps out quickly and coasting is limited

        self.static_friction = 0.20  # [Nm], some static friction to prevent coasting

    def update(self, torque: float) -> float:
        """

        :param torque: Input torque [Nm]
        :return: New angle
        """

        # Compute static friction:

        friction = 0
        if self._velocity > 0.0:
            friction = self.static_friction
        elif self._velocity < 0.0:
            friction = -self.static_friction

        acceleration = (torque - friction -
                        self.damping * self._velocity) / self.inertia

        self._velocity += acceleration * self._dt
        self._angle += self._velocity * self._dt

        # Angle limits:
        lim_min = -90
        lim_max = 75
        if self._angle < lim_min:
            self._angle = lim_min
            self._velocity = 0.0
        if self._angle > lim_max:
            self._angle = lim_max
            self._velocity = 0.0

        return self._angle

    @property
    def angle(self) -> float:
        return self._angle

    @property
    def velocity(self) -> float:
        return self._velocity