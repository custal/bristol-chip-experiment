"""This file is for reading the data files into data structures and plotting them out"""
# %%
import numpy as np
import seaborn as sns
import pandas as pd
from pathlib import Path

from typing import Union

root = Path(__file__).parents[1]
data_directory = root/"Data"


def read_txt(filename: str, headers: bool = True):
    """
    Reads the .txt file into an array in preparation for data analysis.
    """
    with open(filename, "r") as f:
        if headers:  # skip first line
            next(f)
        data = []
        for line in f:
            data.append(float(line.rstrip()))

    return data


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

# %%
