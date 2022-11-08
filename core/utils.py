""" File to hold utility functions """

unit_conversion = {"NM": 1e-9, "UM": 1e-6, "MM": 1e-3, "THZ": 1e12, "GHZ": 1e9, "MHZ": 1e6, "KHZ": 1e3}
c = 299792458


def frequency_to_wavelength(frequency: float, frequency_unit: str, wavelength_unit: str):
    return c / (frequency * unit_conversion[frequency_unit] * unit_conversion[wavelength_unit])

def wavelength_to_frequency(wavelength: float, wavelength_unit: str, frequency_unit: str):
    return c / (wavelength * unit_conversion[frequency_unit] * unit_conversion[wavelength_unit])