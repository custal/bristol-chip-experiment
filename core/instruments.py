""" This file is for functions and classes used to connect to the instruments """

from pyvisa import ResourceManager
from pyvisa.resources import TCPIPInstrument, USBInstrument, SerialInstrument
from pyvisa.errors import VisaIOError
import time
import numpy as np

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
    """
        Wrapper class for managing the Tunics Plus laser
        Tunics Plus laser SCPI commands can be found in the docs folder.
    """
    def __init__(self, resource_name: str = 'TCPIP0::192.168.101.201::inst0::INSTR', power: float = 7.5):
        super().__init__(resource_name)

        if not isinstance(self.instrument, TCPIPInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {TCPIPInstrument}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self.power_unit = "DBM"
        self.resolution = 0.001 # WARNING: This is in nm and doesn't consider wavelength_unit
        self.max_wait_time = 25 #supposed to calibrate in <25s for quantifi laser
        self.name = "QUANTIFI"

        self.source = ":SOURCE1"
        self.output = ":OUTP1"
        self.channel = ":CHAN1"
        
        self.set_power(power) #default power is 10


    @property
    def source_prefix(self):
        return self.source + self.channel

    @property
    def output_prefix(self):
        return self.output + self.channel

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
        """ param (str):
                        MIN: Return the minimum programmable value
                        MAX: Return the maximum programmable value
                        DEF: Return the default value of frequency
                        SET: Return the set value (default) of the frequency in the GRID
                        ACT: Return the actual value of the SET frequency
                        LOCK: Query whether the laser is currently at the SET frequency
                        ALL: Returns all of the above parameters
        ref manual pg. 51
        """
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
        """ param (str):
                        MIN: Return the minimum programmable value
                        MAX: Return the maximum programmable value
                        DEF: Return the default value of wavelength
                        SET: Return the set value (default) of the wavelength in the GRID
                        ACT: Return the actual value of the SET wavelength
                        LOCK: Query whether the laser is currently at the SET wavelength
                        ALL: Returns all of the above parameters
            ref manual pg. 51
        """
        return float(self._send_message(f"{self.source_prefix}:WAV? {param}")) / unit_conversion[self.wavelength_unit]

    def set_power(self, power: float):
        if power < (min_power := self.get_power("MIN")):
            raise ValueError(f"Power '{power} {self.power_unit}' "
                             f"is below laser minimum '{min_power} {self.power_unit}'")
        elif power > (max_power := self.get_power("MAX")):
            raise ValueError(f"Power '{power} {self.power_unit}' "
                             f"is above laser maximum '{max_power} {self.power_unit}'")

        self._send_message(f"{self.source_prefix}:POW {power} {self.power_unit}", read=False)
        self._defined_power = power

    def check_steady_state(self,res = 3):
        return np.round(self.get_power("SET"), res) == np.round(self.get_power("ACT"), res)

    def wait_steady_state(self):
        """
        Checks if laser has reached steady state every 1 second by comparing the set and current
        powers.
        """
        elapsed_time = 0
        delay_time = 1
        while elapsed_time < self.max_wait_time:
            if self.check_steady_state():
                return True
            time.sleep(delay_time)
            elapsed_time+=delay_time
        
        return False

    def shift_power(self, power_shift: float):
        power = self.get_power()
        self.set_power(power + power_shift)

    def get_power(self, param: str = ""):
        """ param (str):
                        MIN: Return the minimum programmable value
                        MAX: Return the maximum programmable value
                        DEF: Return the default value of power
                        SET: Return the desired set value
                        ACT: Return the current value (default)
                        ALL: Returns all of the above parameters

            ref manual pg. 50
        """
        return float(self._send_message(f"{self.source_prefix}:POW? {param}"))

    def set_state(self, state: bool):
        self._send_message(f"{self.output_prefix}:STATE {'ON' if state else 'OFF'}", read=False)

    def get_state(self):
        state = self._send_message(f"{self.output_prefix}:STATE?")
        return True if state == "ON" else False


class TunicsManager(InstrumentManager):
    """
        Wrapper class for managing the Quantifi laser
        Quantifi laser SCPI commands can be found in the docs folder. The manual is for the Tunics T100S-HP not the
        Tunics Plus but the commands should be similar.
    """

    def __init__(self, resource_name: str = 'ASRL4::INSTR', power: float = 0):
        super().__init__(resource_name)

        if not isinstance(self.instrument, SerialInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {SerialInstrument}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "GHZ"
        self._power_unit = "DBM"
        self.resolution = 0.001  # WARNING: This is in nm and doesn't consider wavelength_unit
        self.max_wait_time = 20
        self.name = "TUNICS"
        self.instrument.read_termination = '\r'

        # Empty the read register of anything from previous uses
        i = 0
        while True:
            try:
                self.instrument.read()
            except VisaIOError as e:
                break
            i += 1
            if i == 100:
                raise TimeoutError("Could not empty the readout register on the Tunics laser after 100 reads")

        self.power_unit = self._power_unit
        self.set_state(True)
        self.set_power(power) # Laser must be on to set power
        self.set_state(False)
        self.defined_power = power


    @property
    def power_unit(self):
        return self._power_unit

    @power_unit.setter
    def power_unit(self, unit: str):
        unit = unit.upper()
        if unit not in ("DBM", "MW"):
            raise ValueError(f"Power unit '{unit}' must be either 'DBM' or 'MW'")

        self._send_message(unit, read=False)
        self._power_unit = unit

    def _send_message(self, message: str, read: bool=True):
        try:
            val = self.instrument.query(message).upper().strip("> ")
            if "=" in val:
                # Assume message is of the form "F?" and return is of the form "> f="
                val = val.strip(f"{message[0]}=")
            self._check_error(val)
            if read:
                return val
        except VisaIOError as e:
            raise IOError(e)

    def _check_error(self, error: str):
        """ Tunics has two possible errors
            COMMANDERROR
            VALUEERROR
        """
        if error == "COMMANDERROR":
            raise IOError("Command Error")
        elif error == "VALUEERROR":
            raise IOError("Value Error")
        else:
            return

    def check_steady_state(self, res=0):
        return np.round(self.get_power(), res) == np.round(self.defined_power, res)

    def wait_steady_state(self):
        """
        Checks if laser has reached steady state every 1 second by comparing the set and current
        powers.
        """
        elapsed_time = 0
        delay_time = 1
        while elapsed_time < self.max_wait_time:
            if self.check_steady_state():
                return True
            time.sleep(delay_time)
            elapsed_time += delay_time

        return False

    def set_frequency(self, frequency: float):
        if frequency < (min_freq := self.get_frequency("MIN")):
            raise ValueError(f"Frequency '{frequency} {self.frequency_unit}' "
                             f"is below laser minimum '{min_freq} {self.frequency_unit}'")
        elif frequency > (max_freq := self.get_frequency("MAX")):
            raise ValueError(f"Frequency '{frequency} {self.frequency_unit}' "
                             f"is above laser maximum '{max_freq} {self.frequency_unit}'")

        self._send_message(f"F={frequency}", read=False)

    def shift_frequency(self, frequency_shift: float):
        frequency = self.get_frequency()
        self.set_frequency(frequency + frequency_shift)

    def get_frequency(self, param: str = ""):
        """ param (str):
                        MIN: Return the minimum programmable value
                        MAX: Return the maximum programmable value
        Parameters hardcoded as Tunics-Plus does not return these values
        """
        if param == "MAX":
            return 199728.5
        elif param == "MIN":
            return 182800.3
        elif param == "":
            return float(self._send_message(f"F? {param}"))
        self._check_error("COMMAND ERROR")

    def set_wavelength(self, wavelength: float):
        if wavelength < (min_wav := self.get_wavelength("MIN")):
            raise ValueError(f"Wavelength '{wavelength} {self.wavelength_unit}' "
                             f"is below laser minimum '{min_wav} {self.wavelength_unit}'")
        elif wavelength > (max_wav := self.get_wavelength("MAX")):
            raise ValueError(f"Wavelength '{wavelength} {self.wavelength_unit}' "
                             f"is above laser maximum '{max_wav} {self.wavelength_unit}'")

        self._send_message(f"L={wavelength}", read=False)

    def shift_wavelength(self, wavelength_shift: float):
        wavelength = self.get_wavelength()
        self.set_wavelength(wavelength + wavelength_shift)

    def get_wavelength(self, param: str = ""):
        """ param (str):
                        MIN: Return the minimum programmable value
                        MAX: Return the maximum programmable value
        Parameters hardcoded as Tunics-Plus does not return these values
        """
        if param == "MAX":
            return 1640
        elif param == "MIN":
            return 1510 # The laser can go lower but then the maximum power drops below what should be possible
        elif param == "":
            return float(self._send_message(f"L?"))
        self._check_error("COMMAND ERROR")

    def set_power(self, power: float):
        if power < (min_power := self.get_power("MIN")):
            raise ValueError(f"Power '{power} {self.power_unit}' "
                             f"is below laser minimum '{min_power} {self.power_unit}'")
        elif power > (max_power := self.get_power("MAX")):
            raise ValueError(f"Power '{power} {self.power_unit}' "
                             f"is above laser maximum '{max_power} {self.power_unit}'")

        self._send_message(f"P={power}", read=False)
        self.defined_power = power

    def shift_power(self, power_shift: float):
        power = self.get_power()
        self.set_power(power + power_shift)

    def get_power(self, param: str = ""):
        """ param (str):
                        MIN: Return the minimum programmable value
                        MAX: Return the maximum programmable value
        Parameters hardcoded as Tunics-Plus does not return these values

        The tunics max power is dependent on the wavelength so this max is to be taken with a pinch of salt.
        For consistent results work with a close to minimum power
        """
        if param == "MAX":
            return 7.1
        elif param == "MIN":
            return -6.88
        elif param == "":
            val = self._send_message(f"P?")
            return -99.99 if val == "DISABLED" else float(val)
        self._check_error("COMMAND ERROR")

    def set_state(self, state: bool):
        self._send_message("ENABLE" if state else "DISABLE")

    def get_state(self):
        val = self._send_message(f"P?")
        return False if val == "DISABLED" else True

    @property
    def _identify(self):
        """ Tunics-Plus does not recognise *IDN? so hard code it's name"""
        return "Tunics-Plus, GNI Nettest The colors of WDM"


class PowerMeterManager(InstrumentManager):
    """ Wrapper class for managing power meter instruments
        Thorlab power meter SCPI commands can be found in the docs folder
    """
    def __init__(self, resource_name: str = 'USB0::0x1313::0x8078::P0010441::INSTR', average: int = 100):
        super().__init__(resource_name)

        if not isinstance(self.instrument, USBInstrument):
            raise TypeError(f"The instrument with name '{resource_name}' is not of type {USBInstrument}.")

        self.wavelength_unit = "NM"
        self.frequency_unit = "THZ"
        self._power_unit = "DBM"
        self.power_unit = self._power_unit

        self.sense = ":SENSE"
        self.correction = ":CORRECTION"
        self.set_average(average)

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

    def set_average(self, average: int):
        self._send_message(f":SENSE:AVERAGE:COUNT {average}", read = False)

    def get_average(self):
        return int( self._send_message(":SENSE:AVERAGE:COUNT?"))

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