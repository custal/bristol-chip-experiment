"""This file is for reading the data files into data structures and plotting them out"""
#%%
import numpy as np
import seaborn as sns
import pandas as pd
def read_txt(filename: str, headers: bool = True):
    """
    Reads the .txt file into an array in preparation for data analysis.
    """
    with open(filename,"r") as f:
        if headers: #skip first line
            next(f)
        data = []
        for line in f:
            data.append(float(line.rstrip()))
    
    return data

def plot_sweep(filename: str, data_dir: str = "../Data/", save_dir:str = "../Graphs/", save:bool = False):
    """
    Function to plot the laser sweeps. Get graph of mean power against wavelength
    """
    path = data_dir+filename
    data = pd.read_csv(path, index_col = 0) #sets the wavelength_nm column as index
    data["mean_dbm"] = data.mean(axis = 1)
    data["variance"] = data.var(axis = 1)
    data["std"]=np.sqrt(data["variance"])
    data["Wavelength(nm)"] = data.index
    sns_plot = sns.relplot(data=data,x="Wavelength(nm)", y = "mean_dbm")
    fig = sns_plot.fig

    if save:
        fig.savefig(fr"{save_dir+filename.split('.')[0]}.png",dpi=600)

# %%
