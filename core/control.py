""" This file is for functions and classes used to control the instruments """
import os
import time
import datetime

from core.instruments import QuantifiManager, PowerMeterManager, TunicsManager
import numpy as np
from datetime import date
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
            args[0].laser.set_state(False)
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
    def perform_wavelength_sweep(self, wavelength_start: float, wavelength_end: float, res: float,
                                 filename: str = None, save: bool = True, verbose: bool = True, reps=1):
        """
        Performs a sweep over the given start/stop frequencies. Returns an array of dBm readings
        from the power meter saved as a binary file.

        Arguments:
        wavelength_start: starting wavelength (inclusive in sweep) of laser in nm
        wavelength_end: ending wavelength (inclusive in sweep) in nm
        res: resolution of scan
        save: if True, will save power_readings as a binary file
        filename: name of file to be saved
        delay: seconds to wait after setting the laser to a new wavelength before taking data from the meter
        verbose: if True, will print current wavelength being scanned, as well as power meter reading
        reps: no. of repetitions to do measure by

        Returns:
        power_readings: array object with dim((reps,steps)) of power readings from the power meter
        If save is true, returns a text file saved as "today+"_laser_sweep_"+filename.txt"
        The text file contains a header line "wavelength_nm power_dbm" followed by lines of the
        laser wavelength and power meter readings.

        Save file naming format:
        {dd-mm-yyyy_hh_mm}_laser_sweep_
        samples_{power meter averages over samples}_
        sensitivity_{power meter wavelength setting}_
        {laser; either TUNICS or QUANTIFI}_{start wavelength, 0dp}_{end wavelength, 0dp}_{steps}_
        {filename}.txt
        """
        start_time = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        scan_range = np.arange(wavelength_start, wavelength_end+res, res)
        power_readings = np.zeros((reps, len(scan_range)))

        # add exceptions
        if scan_range[1]-scan_range[0] <= self.laser.resolution:  # 1pm laser resolution
            raise Exception(
                f"Wavelength increase of {scan_range[1]-scan_range[0]} nm is below laser resolution")

        if verbose:
            print("-----Conducting laser sweep-----")
            print("Parameters:-----------")
            print("Laser start/stop/res:", wavelength_start, wavelength_end, res)
            print("Reps:", reps)
            print(
                f"Power meter averaging over {self.power_meter.get_average()} samples")
            print(
                f"Power meter frequency set to {self.power_meter.get_wavelength()} nm")
            print("----------------------")
        for i, wavelength in enumerate(scan_range):

            self.laser.set_wavelength(wavelength)
            # time.sleep(1) # <20 is okay for Quantifi
            if self.laser.wait_steady_state() == True:
                for j in range(reps):
                    power_readings[j, i] = self.power_meter.read()
            else:
                raise Exception(
                    f"Laser has taken more than {self.laser.max_wait_time}s to stabilise")

            if verbose:
                print("Current laser frequency:", wavelength)
                print("Power meter reading:", power_readings[:, i])
                print("----------------------")

        if save:  # save the file
            save_dir = f"../Data/{datetime.datetime.now().strftime('%d-%m-%Y')}/"
            savefile_name = fr"{save_dir}{start_time}_laser_sweep_samples_{str(self.power_meter.get_average())}" +\
                fr"_sensitivity_{str(int(self.power_meter.get_wavelength()))}_" +\
                fr"{self.laser.name}_{round(wavelength_start)}_{round(wavelength_end)}_{len(scan_range)}{'_'+filename if filename else ''}.txt"

            if not os.path.exists(save_dir):
                print("Today's directory not found. Creating new one...")
                os.makedirs(save_dir)

            with open(savefile_name, "w") as f:

                # write the header
                f.write("wavelength_nm ")
                for j in range(reps):
                    f.write(f",power_reading_{str(j)}_dbm ")
                f.write("\n")

                # write the power meter readings
                for i in range(len(scan_range)):
                    f.write(str(scan_range[i]))
                    for j in range(reps):
                        f.write(", "+str(power_readings[j, i]))
                    f.write("\n")
                f.close()

        if verbose:
            if save:
                print("Sweep completed, data saved under", savefile_name)
            else:
                print("Sweep completed")
        return power_readings


if __name__ == "__main__":
    from core.utils import MockInstrument

    laser = TunicsManager('ASRL5::INSTR')  # min 1527.605 max 1568.773
    power_meter = PowerMeterManager()
    setup = ExperimentalSetUp(laser, power_meter)
    start = 1557.5
    stop = 1562.5
    res = 0.001
    start = 1560
    stop = 1560.3
    step = 0.5
    savename = "ring13_finer"
    savename = "test"
    # print("Scan range:",np.arange(start, stop+res, res)[:5],"...",np.arange(start,stop+res,res)[-5:])

    result = setup.perform_wavelength_sweep(
        start, stop, res, filename=savename, reps=10)
    print(result)
