#%%
"""
This script is for me to test random stuff I come across in the project.
"""
import numpy as np
#%%

def FSR_resonance(r:float, laser_wavelength:float = 1550, n:float = 3.48):
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

#%%
ring_radii=np.array([40,80,120,160,200,240,280])/2
DWDM_res = 0.8
print(FSR_resonance(ring_radii))
print(FSR_resonance(ring_radii)>DWDM_res) #only radii up to 120 can be detected using DWDM
