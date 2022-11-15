""" This file is for functions and classes used to control the instruments """

from .instruments import QuantifiManager, PowerMeterManager
import numpy as np
from datetime import date
import time
today = str(date.today())

def laser_control(func):
    """ Decorator to be used on methods in ExperimentalSetup where the laser should be turned on. This decorator will
    turn on the laser at the start of method execution then turn it off at the end. If an error occurs mid-execution
    then the laser will be switched off before the error is raised """
    def error_handler(*args, **kwargs):
        try:
            args[0].laser.set_state(True)
            val = func(*args, **kwargs)
        except Exception as e:
            laser.set_state(False)
            raise e
        args[0].laser.set_state(False)
        return val
    return error_handler


class ExperimentalSetUp:
    """ Class used to handle the experimental setup of a laser with a power meter """
    
    def __init__(self, laser: QuantifiManager, power_meter: PowerMeterManager):

        self.laser = laser
        self.power_meter = power_meter

    @laser_control
    def perform_wavelength_sweep(self, wavelength_start: float, wavelength_end: float, steps: int,
    delay = 25, filename:str = "", save: bool = True, verbose: bool = True):
        """
        Performs a sweep over the given start/stop frequencies. Returns an array of dBm readings
        from the power meter saved as a binary file.

        Arguments:
        wavelength_start: starting wavelength (inclusive in sweep) of laser in nm
        wavelength_end: ending wavelength (inclusive in sweep) in nm
        steps: no. of data points
        save: if True, will save power_readings as a binary file
        filename: name of file to be saved
        delay: seconds to wait after setting the laser to a new wavelength before taking data from the meter
        verbose: if True, will print current wavelength being scanned, as well as power meter reading

        Returns:
        power_readings: array object with dim(steps) of power readings from the power meter
        If save is true, returns a text file saved as "today+"_laser_sweep_"+filename.txt"
        The text file contains a header line "wavelength_nm power_dbm" followed by lines of the
        laser wavelength and power meter readings.

        """
        power_readings = np.zeros(steps)

        scan_range = np.linspace(wavelength_start, wavelength_end, steps)

        #add exceptions
        if scan_range[1]-scan_range[0] <= self.laser.resolution: #1pm laser resolution
            raise Exception(f"Wavelength increase of {scan_range[1]-scan_range[0]} nm is below laser resolution")
        
        if verbose:
            print("-----Conducting laser sweep")
            print("Parameters:-----------")
            print("Laser start/stop/steps:", wavelength_start, wavelength_end, steps)
            print("Delay before measurement:", delay)
            print("----------------------")
        for i, wavelength in enumerate(scan_range):

            self.laser.set_wavelength(wavelength)
            if self.laser.wait_steady_state() == True:
                power_readings[i] = self.power_meter.read()
            else:
                raise Exception(f"Laser has taken more than {self.laser.max_wait_time} to stabilise")
            
            if verbose:
                print("Current laser frequency:", wavelength)
                print("Power meter reading:", power_readings[i])
                print("----------------------")
        if save:
            with open(today+"_laser_sweep_"+filename+".txt","w") as f:

                #write the header
                f.write("wavelength_nm power_dbm\n")

                #write the power meter readings
                for i,power in enumerate(power_readings):
                    f.write(wavelength[i]+","+power+"\n")
                f.close()
        
        if verbose:
            if save:
                print("Sweep completed, data saved under",today+"_laser_sweep_"+filename+".txt")
            else:
                print("Sweep completed")
        return power_readings
            



if __name__ == "__main__":
    from utils import MockInstrument

    laser = QuantifiManager()
    power_meter = PowerMeterManager()
    setup = ExperimentalSetUp(laser, power_meter)

    result = setup.perform_wavelength_sweep(1450, 1555, 16)
    print(result)