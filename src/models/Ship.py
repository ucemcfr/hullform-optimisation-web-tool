import numpy as np

from src.database import Database
from src.models.motions import calculate_jensen_acceleration
from src.models.resistance import calculate_holtrop_resistance


class Ship(object):

    # Ship object to contain parameters
    # Propeller object containing prop params
    # Engine object containing engine params
    # Calculate stability
    # Calculate resistance
    # Calculate seakeeping
    # Calculate weights
    # Calculate stability
    # Method for optimising dimensions
    # Method for optimising prop and engine

    kin_visc = 0.00114
    rho = 1025  # what is rho?
    g = 9.81  # m/s/s

    def __init__(self, velocity, lwl, loa, bwl, boa, draft, vol_disp, lcb, c_m, c_wp, heading, vcb=None, total_resistance=None, km=None, max_vert_acceleration=None):
        self.lwl = lwl
        self.loa = loa
        self.bwl = bwl
        self.boa = boa
        self.draft = draft

        self.vol_disp = vol_disp
        self.lcb = lcb
        self.vcb = vcb  # this is distance below waterline
        self.velocity = velocity  # not sure if this is needed or it will be set outside of the instance
        self.c_m = c_m
        self.c_wp = c_wp
        self.heading = heading

        self.a_wp = c_wp * lwl * bwl
        self.a_m = bwl * draft * c_m
        self.c_b = vol_disp / (lwl * bwl * draft)
        self.c_p = vol_disp / (self.a_m * lwl)
        self.f_n = velocity / np.sqrt(9.807 * lwl)
        self.r_n = (velocity * lwl) / self.kin_visc  # define kinvisc

        self.total_resistance = total_resistance
        self.km = km
        self.max_vert_acceleration = max_vert_acceleration
        # motions (max acceleration, time at max acceleration?) what exactly do I want/need?

    def calculate_resistance(self):
        total_resistance = calculate_holtrop_resistance(self.lwl, self.bwl, self.draft, self.lcb, self.vol_disp, self.velocity, self.r_n, self.f_n, self.c_b, self.c_p, self.c_m, self.c_wp, self.rho, self.g)
        self.total_resistance = total_resistance  # I think this is the wrong thing to do, can't remember why tho
        return

    def calculate_stability(self):
        c_wi = 12 / (self.c_wp ** 2)  # NOTE THIS IS APPROXIMATE
        I = (self.lwl * self.bwl ** 3) / c_wi

        if self.vcb is None:
            self.vcb = (1 / 3) * ((self.draft / 2) + (self.vol_disp / self.a_wp))  # Using Morrish's rule. Distance measured FROM WATERLINE DOWNWARDS

        bm = I / self.vol_disp
        kb = self.draft - self.vcb
        self.km = bm + kb
        return

    def calculate_motions(self):
        self.max_vert_acceleration = calculate_jensen_acceleration(self.lwl, self.bwl, self.draft, self.f_n, self.c_b, self.g, self.heading, 1, 0)  # this last parameter is the longitudinal position for motions, should be able to pass a parameter for this rather than using the default
        return

    def calculate_weights(self):
       pass
        # this is fundamentally different, it is estimating weights based on the case? rather than being an inherent property of the design? at least not in the same way as length, beam etc.

    def save_to_mongo(self):
        Database.insert(collection='previous_designs',
                        data=self.json())


