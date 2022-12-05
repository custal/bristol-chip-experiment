""" This file is for functions and classes used to control the instruments """
import os
import time
import datetime

from core.instruments import QuantifiManager, PowerMeterManager, TunicsManager
from core.analysis import data_directory, plot_sweep, get_minima
import numpy as np


import os


def laser_control(func):
    """ Decorator to be used on methods in ExperimentalSetup where the laser should be turned on. This decorator will
    turn on the laser at the start of method execution then turn it off at the end. If an error occurs mid-execution
    then the laser will be switched off before the error is raised """
    def error_handler(*args, **kwargs):
        try:
            args[0].laser.set_state(True)
            val = func(*args, **kwargs)
        except (Exception, KeyboardInterrupt) as e:
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
    def perform_wavelength_sweep(self, wavelength_start: float, wavelength_end: float, res: float, graph: bool = True,
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
            raise ValueError(
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
                raise TimeoutError(
                    f"Laser has taken more than {self.laser.max_wait_time}s to stabilise")

            if verbose:
                print("Current laser frequency:", wavelength)
                print("Power meter reading:", power_readings[:, i])
                print("----------------------")

        if save:  # save the file
            today_directory = datetime.datetime.now().strftime('%d-%m-%Y')
            save_dir = data_directory/today_directory
            savefile_name = fr"{start_time}_laser_sweep_samples_{str(self.power_meter.get_average())}" +\
                fr"_sensitivity_{str(int(self.power_meter.get_wavelength()))}_" +\
                fr"{self.laser.name}_{round(wavelength_start)}_{round(wavelength_end)}_{len(scan_range)}{'_'+filename if filename else ''}.txt"
            save_path = save_dir/savefile_name

            if not os.path.exists(save_dir):
                print("Today's directory not found. Creating new one...")
                os.makedirs(save_dir)

            with open(save_path, "w") as f:

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
            if graph:
                plot_sweep(f"{today_directory}/{savefile_name}",
                           "" if filename is None else filename, True)
        if verbose:
            if save:
                print("Sweep completed, data saved under", savefile_name)
            else:
                print("Sweep completed")
        return power_readings

    @laser_control
    def resonance_finding(self, resonance_rough, width: float = 0.15, graph: bool = True, res: float = 0.001,
                          filename: str = None, reps: int = 10, verbose: bool = True):
        """
        Given a list of points that resonances are roughly supposed to be, do a scan to get the actual resonance.
        Saves the data by default.

        Arguments:
        resonance_rough: list of points where the resonances occur. Obtain from a coarse scan. Try to centre
        width: float in nm, determines the scan range around the points that we will do. Default 0.15 from past data
        graph: bool, if True, plot final graph
        verbose: bool, if True, prints data as it is collected
        reps: no. of data readings
        """
        start_time = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
        today_directory = datetime.datetime.now().strftime('%d-%m-%Y')
        save_dir = data_directory/today_directory
        savefile_name = fr"{start_time}_resonance_finding_samples_{str(self.power_meter.get_average())}" +\
            fr"_sensitivity_{str(int(self.power_meter.get_wavelength()))}_" +\
            fr"{self.laser.name}_{str(len(resonance_rough))}{'_'+filename if filename else ''}.txt"
        save_path = save_dir/savefile_name

        if not os.path.exists(save_dir):
            print("Today's directory not found. Creating new one...")
            os.makedirs(save_dir)

        with open(save_path, "w") as f:

            # write the header
            f.write("wavelength_nm ")
            for j in range(reps):
                f.write(f",power_reading_{str(j)}_dbm ")
            f.write("\n")

            for i, wavelength in enumerate(resonance_rough):
                curr_wavelength_scan = np.arange(
                    wavelength-width, wavelength+width+res, res)

                for j, curr_wavelength in enumerate(curr_wavelength_scan):
                    try:
                        self.laser.set_wavelength(curr_wavelength)
                        f.write(str(curr_wavelength))
                        if self.laser.wait_steady_state() == True:
                            readings = []
                            for k in range(reps):
                                curr_reading = self.power_meter.read()
                                f.write(", "+str(curr_reading))
                                readings.append(curr_reading)
                            f.write("\n")
                            if verbose:
                                print(
                                    f"Resonance {i+1} of {len(resonance_rough)} Frequency {curr_wavelength}")
                                print("Power meter reading:", readings)
                                print("----------------------")
                        else:
                            raise Exception(
                                f"Laser has taken more than {self.laser.max_wait_time}s to stabilise")
                    except:
                        print(
                            f"Sweep failed at {str(curr_wavelength)}nm sweep for resonance {str(i)}")
                        f.close()
            if graph:
                plot_sweep(f"{today_directory}/{savefile_name}",
                           "" if filename is None else filename, True)
        print("Sweep completed, data saved under", savefile_name)
        return True


if __name__ == "__main__":
    from core.utils import MockInstrument

    laser = TunicsManager('ASRL6::INSTR')  # min 1527.605 max 1568.773
    power_meter = PowerMeterManager()
    setup = ExperimentalSetUp(laser, power_meter)
    start = 1539
    stop = 1571
    res = 0.002

    savename = "ring_10_fine_scan"
    # savename = "test"
    # print("Scan range:",np.arange(start, stop+res, res)[:5],"...",np.arange(start,stop+res,res)[-5:])

    # result = setup.perform_wavelength_sweep(
    #     start, stop, res, filename=savename, reps=10)

    # example use of resonance finding code
    # savename = "test_resonance_finding"
    coarse_start = 1539
    coarse_stop = 1571
    res = 0.1
    coarse_wavelengths = np.arange(coarse_start, coarse_stop, res)
    coarse_power_readings = setup.perform_wavelength_sweep(
        coarse_start, coarse_stop, res, filename="TAILAI_loopback_66", reps=10)

    # minima, resonances = setup.get_minima(
    #     coarse_power_readings, coarse_wavelengths, width=15)
    # setup.resonance_finding(resonances)
