""" This file is for functions and classes used to connect to the instruments """

from pyvisa import ResourceManager
from pyvisa.resources import TCPIPInstrument
from pyvisa.errors import VisaIOError

from core.utils import frequency_to_wavelength, wavelength_to_frequency, unit_conversion

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
    def __init__(self, resource_name: str = 'TCPIP0::192.168.101.201::inst0::INSTR'):
        super().__init__(resource_name)

        if not isinstance(self.instrument, TCPIPInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {TCPIPInstrument}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self.power_unit = "DBM"

        self.source = ":SOURCE1"
        self.output = ":OUTP1"
        self.channel = ":CHAN1"

    @property
    def source_prefix(self):
        return self.source + self.channel

    @property
    def output_prefix(self):
        return self.output + self.channel

    def set_frequency(self, frequency: float):
        self._send_message(f"{self.source_prefix}:FREQ {frequency} {self.frequency_unit}", read=False)

    def shift_frequency(self, frequency_shift: float):
        frequency = self.get_frequency()
        self.set_frequency(frequency + frequency_shift)

    def get_frequency(self):
        return float(self._send_message(f"{self.source_prefix}:FREQ?")) / unit_conversion[self.frequency_unit]

    def set_wavelength(self, wavelength: float):
        self._send_message(f"{self.source_prefix}:WAV {wavelength} {self.wavelength_unit}", read=False)

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self):
        return float(self._send_message(f"{self.source_prefix}:WAV?")) / unit_conversion[self.wavelength_unit]

    def set_power(self, power: float):
        self._send_message(f"{self.source_prefix}:POW {power} {self.power_unit}", read=False)

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
    def __init__(self, resource_name: str = None):
        super().__init__(resource_name)

        if not isinstance(self.instrument, None):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {None}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self.power_unit = "DBM"

        self.source = ":SOURCE1"
        self.output = ":OUTP1"
        self.channel = ":CHAN1"

    @property
    def source_prefix(self):
        return self.source + self.channel

    @property
    def output_prefix(self):
        return self.output + self.channel

    def set_frequency(self, frequency: float):
        self._send_message(f"{self.source_prefix}:FREQ {frequency} {self.frequency_unit}", read=False)

    def shift_frequency(self, frequency_shift: float):
        frequency = self.get_frequency()
        self.set_frequency(frequency + frequency_shift)

    def get_frequency(self):
        return float(self._send_message(f"{self.source_prefix}:FREQ?")) / unit_conversion[self.frequency_unit]

    def set_wavelength(self, wavelength: float):
        self._send_message(f"{self.source_prefix}:WAV {wavelength} {self.wavelength_unit}", read=False)

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self):
        return float(self._send_message(f"{self.source_prefix}:WAV?")) / unit_conversion[self.wavelength_unit]

    def read(self):
        pass


if __name__ == "__main__":
    laser = QuantifiManager()