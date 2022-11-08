""" This file is for functions and classes used to control the instruments """

from core.instruments import QuantifiManager, PowerMeterManager
import numpy as np

from core.utils import frequency_to_wavelength

class ExperimentalSetUp:
    """ Class used to handle the experimental setup of a laser with a power meter """

    def __init__(self, laser: LaserManager, power_meter: PowerMeterManager):

        self.laser = laser
        self.power_meter = power_meter

    def perform_wavelength_sweep(self, wavelength_start: float, wavelength_end: float, step: float):
        for wavelength in np.linspace(wavelength_start, wavelength_end, step):
            self.laser.set_wavelength(wavelength)
            self.power_meter.take_measurement