""" File to hold utility functions """

unit_conversion = {"NM": 1e-9, "UM": 1e-6, "MM": 1e-3, "THZ": 1e12, "GHZ": 1e9, "MHZ": 1e6, "KHZ": 1e3}
c = 299792458


def frequency_to_wavelength(frequency: float, frequency_unit: str, wavelength_unit: str):
    return c / (frequency * unit_conversion[frequency_unit] * unit_conversion[wavelength_unit])

def wavelength_to_frequency(wavelength: float, wavelength_unit: str, frequency_unit: str):
    return c / (wavelength * unit_conversion[frequency_unit] * unit_conversion[wavelength_unit])


class MockInstrument:
    """ This is a mock class used to test the analysis if not connected to live instruments """
    def __init__(self):

        self.state = False
        self.wavelength = 1550
        self.power = 7.5
        self.resolution = 0.01

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