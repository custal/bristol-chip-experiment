# bristol-chip-experiment
This repositroy is used to communicate with lab equipment using pyvisa. The classes created within will be used to perform sweep analysis over the equipment parameters


This project uses poetry to manage packages. You can install poetry here:
https://python-poetry.org/

If you are using an alternative package manager, such as conda, you can add all the packages in the 
pyproject.toml file which are listed under tool.poetry.dependencies to your environment. We then need to install this 
package to your environment. Delete pyproject.toml and run `pip install -e .` while in the top level directory. Your
code should now run.

In order for pyvisa to work on your machine you will need to install NI-MAX. You will also need to configure it to 
recognise the Quantifi laser. The following steps will show you how to do this.

**Installing pyVISA** \
Installation instructions can be found here: https://pyvisa.readthedocs.io/en/latest/introduction/getting.html

Steps I took to install on my Windows 10 laptop:
1. pip install pyvia
2. Install the NI-VISA backend (OS: Windows,  version: 2202 Q3) https://www.ni.com/en-gb/support/downloads/drivers/download.ni-visa.html#460225
3. Check the backend is installed by running:
```
Import pyvisa
rm=pyvisa.ResourceManager()
rm.list_resources()
```
	
If this runs without error then you have installed pyvisa and NI-VISA correctly

**Connecting to the laser** 
1. Plug the laser USB into your device, drivers should then automatically install
2. Run the code:

```
Import pyvisa
rm=pyvisa.ResourceManager()
rm.list_resources()
```
	
You should see the output ('ASRLn::INSTR',)
3. Even if the resource manager has picked up the device you may not be able to connect. Check you can connect to the laser by running ping <laser ip address> in the Windows CMD or by putting the IP address into a browser. If you cannot connect then you may not have installed the drivers correctly. You can get the drivers from https://www.quantifiphotonics.com/resources/drivers-software-and-manuals/matriq-resources/ . I installed the top option "CohesionOperator-3.00.10.zip".
   When you do this you will no longer be able to see the laser in the resource list.
4. To connect to the Quantifi laser we need to make a TCPIP address for it. We do this by opening NI-MAX (installed in the first step)
5. Go to My system -> Devices and interfaces -> Network devices
6. Select Add Network Device at the top
7. Input the laser IP into Manual entry of LAN instrument and Validate.
You should now be able to find the laser in the pyvisa resource manager and open the resource