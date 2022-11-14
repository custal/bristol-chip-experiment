""" This file is for functions and classes used to connect to the instruments """

from pyvisa import ResourceManager
from pyvisa.resources import TCPIPInstrument, USBInstrument
from pyvisa.errors import VisaIOError

from utils import frequency_to_wavelength, wavelength_to_frequency, unit_conversion

rm = ResourceManager()

class InstrumentManager:
    """ Wrapper class for managing instruments """

    def __init__(self, resource_name: str):
        self.instrument = rm.open_resource(resource_name)

    def _send_message(self, message: str, read: bool=True):
        try:
            if read:
                return self.instrument.query(message).strip("\n")
            else:
                self.instrument.write(message)
        except VisaIOError as e:
            self._check_error()
            raise IOError(e)

    def _check_error(self):
        """ '*ESR?' to check standard event Status Register. This will show any errors
        5: Command Error 32
        4: Execution Error 16
        3: Device dependent Error 8
        """
        error = int(self.instrument.query("*ESR?"))
        if error == 32:
            raise IOError("Command Error")
        elif error == 16:
            raise IOError("Execution Error")
        elif error == 8:
            raise IOError("Device Dependent Error")
        else:
            return

    def _check_operation_queue(self):
        """ '*OPC?' to check the operation queue

        1 is returned if all the modules installed in the chassis are ready to execute commands
        0 is returned if any module installed in the chassis still has a command to execute in the
        input queue
        """
        return self._send_message('*OPC?')

    @property
    def _identify(self):
        return self._send_message("*IDN?")

    def __repr__(self):
        return f"<{self._identify}, {self.instrument}>"


class QuantifiManager(InstrumentManager):
    """
        Wrapper class for managing the Quantifi laser
        Quantifi laser SCPI commands can be found here:
        https://cdn.quantifiphotonics.com/20220329110339/Laser_1000_Series_UserManual_V4p04.pdf
    """
    def __init__(self, resource_name: str = 'TCPIP0::192.168.101.201::inst0::INSTR'):
        super().__init__(resource_name)

        if not isinstance(self.instrument, TCPIPInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {TCPIPInstrument}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self.power_unit = "DBM"
        self.resolution = 0.001 # WARNING: This is in nm and doesn't consider wavelength_unit
        self.defined_power = 10.0 #in dBm

        self.source = ":SOURCE1"
        self.output = ":OUTP1"
        self.channel = ":CHAN1"
        
        self.set_power(7.5) #default power is 10


    @property
    def source_prefix(self):
        return self.source + self.channel

    @property
    def output_prefix(self):
        return self.output + self.channel

    def get_min_wavelength(self):
        return float(self._send_message(f"{self.source_prefix}:WAV? MIN")) / unit_conversion[self.wavelength_unit]

    def get_max_wavelength(self):
        return float(self._send_message(f"{self.source_prefix}:WAV? MAX")) / unit_conversion[self.wavelength_unit]

    def set_frequency(self, frequency: float):
        if frequency < (min_freq := self.get_frequency("MIN")):
            raise ValueError(f"Frequency '{frequency} {self.frequency_unit}' "
                             f"is below laser minimum '{min_freq} {self.frequency_unit}'")
        elif frequency > (max_freq := self.get_frequency("MAX")):
            raise ValueError(f"Frequency '{frequency} {self.frequency_unit}' "
                             f"is above laser maximum '{max_freq} {self.frequency_unit}'")

        self._send_message(f"{self.source_prefix}:FREQ {frequency} {self.frequency_unit}", read=False)

    def shift_frequency(self, frequency_shift: float):
        frequency = self.get_frequency()
        self.set_frequency(frequency + frequency_shift)

    def get_frequency(self, param: str = ""):
        return float(self._send_message(f"{self.source_prefix}:FREQ? {param}")) / unit_conversion[self.frequency_unit]

    def set_wavelength(self, wavelength: float):
        if wavelength < (min_wav := self.get_wavelength("MIN")):
            raise ValueError(f"Wavelength '{wavelength} {self.wavelength_unit}' "
                             f"is below laser minimum '{min_wav} {self.wavelength_unit}'")
        elif wavelength > (max_wav := self.get_wavelength("MAX")):
            raise ValueError(f"Wavelength '{wavelength} {self.wavelength_unit}' "
                             f"is above laser maximum '{max_wav} {self.wavelength_unit}'")

        self._send_message(f"{self.source_prefix}:WAV {wavelength} {self.wavelength_unit}", read=False)

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self, param: str = ""):
        return float(self._send_message(f"{self.source_prefix}:WAV? {param}")) / unit_conversion[self.wavelength_unit]

    def set_power(self, power: float):
        self._send_message(f"{self.source_prefix}:POW {power} {self.power_unit}", read=False)
        self.defined_power = power

    def shift_power(self, power_shift: float):
        power = self.get_power()
        self.set_power(power + power_shift)

    def get_power(self):
        return float(self._send_message(f"{self.source_prefix}:POW?"))

    def set_state(self, state: bool):
        self._send_message(f"{self.output_prefix}:STATE {'ON' if state else 'OFF'}", read=False)

    def get_state(self):
        state = self._send_message(f"{self.output_prefix}:STATE?")
        return True if state == "ON" else False


class PowerMeterManager(InstrumentManager):
    """ Wrapper class for managing power meter instruments
        Thorlab power meter SCPI commands can be found here:
        https://www.thorlabs.com/drawings/3c723420dbbe302b-628E3525-E1CC-62FF-6BDFDA05526B9FE3/PM100D-Manual.pdf
    """
    def __init__(self, resource_name: str = 'USB0::0x1313::0x8078::P0010441::INSTR'):
        super().__init__(resource_name)

        if not isinstance(self.instrument, USBInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {USBInstrument}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self._power_unit = "DBM"
        self.power_unit = self._power_unit

        self.sense = ":SENSE"
        self.correction = ":CORRECTION"

    @property
    def sense_prefix(self):
        return self.sense + self.correction

    @property
    def power_unit(self):
        return self._power_unit

    @power_unit.setter
    def power_unit(self, unit: str):
        unit = unit.upper()
        if unit not in ("DBM", "W"):
            raise ValueError(f"Power unit '{unit}' must be either 'DBM' or 'W'")

        self._send_message(f":SENSE:POWER:DC:UNIT {unit}", read=False)
        self._send_message("Configure:Scalar:POWer", read=False)
        self._power_unit = unit

    def set_wavelength(self, wavelength: float):
        self._send_message(f"{self.sense_prefix}:WAV {wavelength} {self.wavelength_unit}", read=False)

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self):
        # The power meter always returns wavelength in units of 'nm'
        return float(self._send_message(f"{self.sense_prefix}:WAV?")) * \
                     unit_conversion[self.wavelength_unit] / unit_conversion["NM"]

    def read(self):
        return self._send_message(":READ?")


if __name__ == "__main__":
    laser = QuantifiManager()