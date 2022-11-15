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
