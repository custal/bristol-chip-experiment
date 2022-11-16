"""This file is for reading the data files into data structures and plotting them out"""
#%%
import numpy as np
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

#%%
import seaborn as sns

data = read_txt("../Data/laser_sweep_154649_154748.txt")
x = np.arange(1546.49,1547.49,0.01)
g = sns.relplot(x = x, y = data)



# %%
import numpy as np
import seaborn as sns
import pandas as pd


# %%
#Plotting the sweep of the QUANTIFI laser
fname = r"../Data/2022-11-16_laser_sweep_powersamples100_pm_sensitivity_1550000_QUANTIFI_powermeter_characterisation.txt"
data = pd.read_csv(fname,index_col = 0)
data["mean_dbm"] = data.mean(axis = 1)
data["variance"] = data.var(axis = 1)
data["std"]=np.sqrt(data["variance"])
data.head()
data.reset_index()
data.head()
data["Wavelength(nm)"] = data.index
sns_plot = sns.relplot(data=data,x="Wavelength(nm)", y = "mean_dbm")
fig = sns_plot.fig
fig.savefig("../Graphs/QUANTIFI_laser_sweep_1550_sensitivity",dpi=600)
# %%
data["variance"]