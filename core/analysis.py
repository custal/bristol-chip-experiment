"""This file is for reading the data files into data structures and plotting them out"""
# %%
import numpy as np
import seaborn as sns
import pandas as pd
from pathlib import Path
from scipy.signal import find_peaks

from typing import Union

root = Path(__file__).parents[1]
data_directory = root/"Data"


def FSR_resonance(r: float, laser_wavelength: float = 1550, n: float = 3.48):
    """
    Function to calculate the free spectral range of the microring resonators
    on the chip

    Arguments:
    laser_wavelength - wavelength in nm
    n - refractive index. Supposed to be group index, but for now can just use
    the index of silicon as a first approx.
    r - radius of the ring in micrometers

    Returns:
    FSR - free spectral range in nm
    """
    L = 2*np.pi*(r/10**6)
    FSR = (laser_wavelength/10**9)**2/(n*L)
    return FSR*10**9


def invert_FSR_resonances(FSR: float, laser_wavelength: float = 1550, n: float = 3.48):
    '''
    Returns the ring radius for the expected FSR

    Arguments:
    laser_wavelength - wavelength in nm
    n - refractive index. Supposed to be group index, but for now can just use
    the index of silicon as a first approx.
    FSR - free spectral range in nm

    Returns:
    d - diameter of the ring in micrometers

    '''

    L = (laser_wavelength/10**9)**2*10**9/(n*FSR)
    d = L/np.pi*10**6

    return d


def freq_to_wavelength(freq):
    """
    Frequency given in Hz
    """
    c = 299792458.0
    wavelength = c/freq

    return wavelength


def get_DWDM_wavelengths(channels: int = 32):
    """
    Returns the DWDM channels we use (21 to 53) as an array of wavelength channels

    Input
    channels: no. of DWDM channels. Starting in the telecom channel 21.
    """

    ch21_f = 192.1  # in GHz

    frequencies = np.arange(ch21_f, ch21_f+channels*0.1, 0.1)*10**12

    wavelengths = np.round(freq_to_wavelength(frequencies)*10**9, 2)
    return wavelengths


def plot_sweep(fname: str, title: str = "", save: bool = True):
    """
    Function to plot the laser sweeps. Get graph of mean power against wavelength
    """
    path = data_directory/fname
    save_path = data_directory/(fname.split('.')[0]+".png")
    # sets the wavelength_nm column as index
    data = pd.read_csv(path, index_col=0)

    data["mean_dbm"] = data.mean(axis=1)
    data["variance"] = data.var(axis=1)
    data["std"] = np.sqrt(data["variance"])
    data["Wavelength(nm)"] = data.index
    sns_plot = sns.relplot(data=data, x="Wavelength(nm)", y="mean_dbm", s=5)
    sns_plot.set_axis_labels("Wavelength (nm)", "Power (dBm)")
    if title:
        sns_plot.set(title=title)

    fig = sns_plot.fig
    if save:
        print(fr"Saving figure to {save_path}")
        fig.savefig(save_path, dpi=600, bbox_inches='tight')


def get_minima(coarse_power, coarse_wavelength, width: float = 15, thr: float = 2):
    """
    Function to return the minima of a coarse ring sweep

    Arguments:
    coarse_power: array of power readings from coarse scan
    coarse_wavelength: wavelength from coarse scan.
    width: bin size of the resonances. Set to 15*(coarse scan resolution) to exclude any minima from the same resonance

    Returns:
    resonances: list of wavelengths where resonances occur. To be fed into resonance_finding function
    minima: indices of wavelength array where resonances occur.
    """

    mean_power = -1*np.array([np.mean(coarse_power[:, i])
                              for i in range(len(coarse_wavelength))])
    minima, _ = find_peaks(mean_power, height=0,
                           distance=width, threshold=thr)
    resonances = coarse_wavelength[minima]
    print(f"Resonances occuring at {resonances} nm")

    return minima, resonances
# %%
