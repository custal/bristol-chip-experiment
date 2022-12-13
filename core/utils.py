""" File to hold utility functions """
import datetime
import os
from core.analysis import data_directory, plot_sweep
import contextlib

unit_conversion = {"NM": 1e-9, "UM": 1e-6, "MM": 1e-3,
                   "THZ": 1e12, "GHZ": 1e9, "MHZ": 1e6, "KHZ": 1e3}
c = 299792458


def frequency_to_wavelength(frequency: float, frequency_unit: str, wavelength_unit: str):
    return c / (frequency * unit_conversion[frequency_unit] * unit_conversion[wavelength_unit])


def wavelength_to_frequency(wavelength: float, wavelength_unit: str, frequency_unit: str):
    return c / (wavelength * unit_conversion[frequency_unit] * unit_conversion[wavelength_unit])

@contextlib.contextmanager
def open_time_stamped_file(filename: str=None, start_time: str=None, graph: bool=True, save: bool=True):
    """ Create a directory for today's date and a file for the time

    Probably a better wya to handle saving as an option but I couldn't think of it in the moment
    """
    today_directory = datetime.datetime.now().strftime('%d-%m-%Y')
    if start_time is None:
        start_time = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    save_dir = data_directory / today_directory
    savefile_name = fr"{start_time}{'_' + filename if filename else ''}.txt"
    save_path = save_dir / savefile_name

    if save:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        file = open(save_path, "w")
        yield file
        file.close()
        print(fr"Saving data to {save_path}")
    else:
        yield None

    if graph:
        plot_sweep(f"{today_directory}/{savefile_name}", filename if filename else "", save=True)



class MockInstrument:
    """ This is a mock class used to test the analysis if not connected to live instruments """

    def __init__(self):

        self.state = False
        self.wavelength = 1550
        self.power = 7.5
        self.resolution = 0.002
        self.name = "mock"

    def wait_steady_state(self):
        return True

    def set_frequency(self, frequency: float):
        self.wavelength = c/frequency

    def shift_frequency(self, frequency_shift: float):
        frequency = self.get_frequency()
        self.set_frequency(frequency + frequency_shift)

    def get_frequency(self):
        return c/self.wavelength

    def set_wavelength(self, wavelength: float):
        self.wavelength = wavelength

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self):
        return self.wavelength

    def get_average(self):
        return self.wavelength

    def set_power(self, power: float):
        self.power = power

    def shift_power(self, power_shift: float):
        power = self.get_power()
        self.set_power(power + power_shift)

    def get_power(self):
        return self.power

    def set_state(self, state: bool):
        self.state = state

    def get_state(self):
        return self.state

    def read(self):
        return self.power
