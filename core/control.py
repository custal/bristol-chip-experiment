""" This file is for functions and classes used to control the instruments """

from core.instruments import QuantifiManager, PowerMeterManager
import numpy as np

class ExperimentalSetUp:
    """ Class used to handle the experimental setup of a laser with a power meter """

    def __init__(self, laser: QuantifiManager, power_meter: PowerMeterManager):

        self.laser = laser
        self.power_meter = power_meter

    def perform_wavelength_sweep(self, wavelength_start: float, wavelength_end: float, step: float):
        for wavelength in np.arange(wavelength_start, wavelength_end, step):
            self.laser.set_wavelength(wavelength)
            self.power_meter.read()

if __name__ == "__main__":
    from core.utils import MockInstrument

    laser = MockInstrument()
    power_meter = MockInstrument()
    setup = ExperimentalSetUp(laser, power_meter)

    result = setup.perform_wavelength_sweep(1450, 1555, 0.5)
    print(result)