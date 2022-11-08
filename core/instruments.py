from pyvisa import ResourceManager
from pyvisa.resources import TCPIPInstrument
from pyvisa.errors import VisaIOError

rm = ResourceManager()

unit_conversion = {"NM": 1e-9, "UM": 1e-6, "MM": 1e-3, "THZ": 1e12, "GHZ": 1e9, "MHZ": 1e6, "KHZ": 1e3}
c = 299792458

class LaserManager:
    """ Wrapper class for managing laser instruments
        Quantifi laser commands can be found here:
        https://cdn.quantifiphotonics.com/20220328111213/O2E_1000-1400_Series_UserManual_V3p06.pdf"""

    def __init__(self, resource_name: str = 'TCPIP0::192.168.101.201::inst0::INSTR'):
        instrument = rm.open_resource(resource_name)

        if not isinstance(instrument, TCPIPInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {TCPIPInstrument}.")

        self.instrument = instrument
        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self.power_unit = "DBM"

    def _send_message(self, message: str):
        try:
            return self.instrument.query(message)
        except VisaIOError as e:
            self._check_error()
            raise VisaIOError(e)

    def _check_error(self):
        """ '*ESR?' to check standard event Status Register. This will show any errors
        5: Command Error 32
        4: Execution Error 16
        3: Device dependent Error 8
        """
        error = int(self.instrument.query("*ESR?"))
        if error == 32:
            raise VisaIOError("Command Error")
        elif error == 16:
            raise VisaIOError("Execution Error")
        elif error == 8:
            raise VisaIOError("Device Dependent Error")
        else:
            return

    def _check_operation_queue(self):
        """ '*OPC?' to check the operation queue

        1 is returned if all the modules installed in the chassis are ready to execute commands
        0 is returned if any module installed in the chassis still has a command to execute in the
        input queue
        """
        self._send_message('*OPC?')

    def _frequency_to_wavelength(self, frequency: float):
        return c / (frequency*unit_conversion[self.frequency_unit]*unit_conversion[self.wavelength_unit])

    def _wavelength_to_frequency(self, wavelength: float):
        return c / (wavelength*unit_conversion[self.frequency_unit]*unit_conversion[self.wavelength_unit])

    def set_frequency(self, frequency: float):
        self.set_wavelength(self._frequency_to_wavelength(frequency))

    def shift_frequency(self, frequency_shift: float):
        self.shift_wavelength(self._frequency_to_wavelength(frequency_shift))

    def get_frequency(self):
        self._wavelength_to_frequency(self.get_wavelength())

    def set_wavelength(self, wavelength: float):
        self._send_message(f"WAVelength {wavelength} {self.wavelength_unit}")

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self):
        return self._send_message("WAVelength?")

    def set_power(self, power: float):
        self._send_message(f"PDPower {power} {self.power_unit}")

    def shift_power(self, power_shift: float):
        power = self.get_power()
        self.set_power(power + power_shift)

    def get_power(self):
        return self._send_message("PDPower?")


if __name__ == "__main__":
    laser = LaserManager()