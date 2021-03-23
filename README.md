# Electric-Car-Racing

For Electric Race Car Simulations, simulating how much
energy it takes to race an electric car around tracks

# Usage

To use this simulation you must have python (3.X) installed on your machine
Once installed simply navigate to the top level of this repo and run `python3 simulation.py`
A UI should appear and results should be plotted, there will also be command line printout
for debugging purposes.

This simulation uses NREL's FASTsim as validation. First results are calculated using this simulation's
calculation methods. Then a custom drive cycle is made from results of this simulation and input to 
FASTsim to validate results.

NREL FASTsim: [link](https://www.nrel.gov/transportation/fastsim.html)
FASTsim validation: [link](https://www.nrel.gov/docs/fy18osti/71168.pdf)

# Present Status?

This is a next iteration at the new App architecture with QThreads and Qt.Core SIGNALs
between the main window and the Race Sim Thread.  It is builds on the the
last working main from Matt AND merging in the concepts from branch
"one-lock-to-rule-them-all" which implements a single read/write lock in the DataStore
access methods to control access to the contained data from the MainWindow and
SimulationThreads.

There is a QApplication which has a custom MainWindow class for hosting application controls
and displaying the graphical results.  The basic architecture utilizes Qthread
and Signal/Slots coordinate activities between the MainWindow and worker threads.

At startup the MainWindow is responsible for starting the worker threads. For this version
there are 2 worker threads - SimulationThread & PlotRefreshThread

- SimulationThread calculates and publishes calculations the actual scientific
results to DataStore object
- PlotRefreshThread is a simple timer thread that periodically signals to the MainWindow
to go retrieve SimulationThread results from the DataStore

For this version the MainWindow user "controls" are two push buttons that say
"Run/Continue" and "Pause". Pressing "Run/Continue" causes the SimulationThread
to emit a signal to be emitted from the Worker thread  after "Run/Continue" is pressed.

This signal from the Worker thread emits is a signal back (with a string of data,
actually a digit) to the mainWindow thread that is received on a main thread slot,
that updates the status text widget "Status" with the signaled data.

A second periodic signal that is emitted from the PlotRefreshThread to the MainWindow
is used as a trigger for the MainWindow to generate a plot. The MainWindow in turn
plots the data in DataStore from 0 to the current simulation_index.

DataStore has been updated to use a single lock for coordinating writes/reads to the 
data store that is shared by the SimulationThread (reader/writer) and the MainWindow 
(thread) which is a read-only consumer of the data. In this intermediate version of 
the code, we're just playing with (sharing) the data store's simulation_index value.

This version of the code is run with the command:
$ python3 simulation.py

And it works!

# Vieweing cProfile simulation results

As of 12/15 the simulation will output a file named `profile.out` using the cProfile module.
These results can be viewed using `runsnake`
The things that I did to get `cProfile` and `runsnake` to work for me are documented here: https://kupczynski.info/2015/01/16/profiling-python-scripts.html

To view do the following things:
## Install runsnake

### On Ubuntu 20.04 Install the runsnake app and associated packages as follows:

$ sudo apt install runsnakerun

### Verify the installation: `which runsnake` should return something in your $PATH

$ which runsnake

## Run runsnake

### call runsnake with `profile.out` as an argument: `runsnake profile.out`

$ runsnake profile.out

### That should do it!

# Car Variables

This simulation uses variables names that are named the same as FASTsim's variables for
car related variables.
Reference: [link](https://www.nrel.gov/transportation/fastsim.html)

## Car Variables

Description of car variables and correlation to FASTsim's variables

### Abbreviations used in FASTsim

| Abbreviation | Meaning |
| ------------ | ------- |
| cur | current time step |
| prev | previous time step |
| cyc | drive cycle |
| secs | seconds |
| mps | meters per second |
| mph | miles per hour |
| kw | kilowatts, unit of power |
| kwh | kilowatt-hour, unit of energy |
| kg | kilograms, unit of mass |
| max | maximum |
| min | minimum |
| avg | average |
| fs | fuel storage (eg. gasoline/diesel tank, pressurized hydrogen tank) |
| fc | fuel converter (eg. internal combustion engine, fuel cell) |
| mc | electric motor/generator and controller |
| ess | energy storage system (eg. high voltage traction battery) |
| chg | charging of a component |
| dis | discharging of a component |
| lim | limit of a component |
| regen | associated with regenerative braking |
| des | desired value |
| ach | achieved value |
| in | component input |
| out | component output |
| UDDS | Urban Dynamometer Driving Schedule |
| val | value |

### Table of Variables

| FASTsim Variable Name | Racing Sim Equivalent | Descripton |
| --------------------- | --------------------- | ---------- |
| dragCoef | drag_coefficient | Drag coefficient (aerodynamic) |
| fronatlAreaM2 | frontal_area | Frontal area of vehicle in meters square (aerodynamic) |
| gliderKg | mass (kind of) | Weight of gliding frame in kg (without other weights listed) |
| vehCgM | - | Height of center of gravity above ground in meters |
| driveAxleWeightFrac | - | Percentage of weight on the drive axle |
| wheelbaseM | - | Wheel base of car in meters |
| cargoKg | mass (kind of) | Weight of cargo in car in kg |
| vehoverrideKg | mass (kind of) | Override weight for vehicle in kg (assumed that this will override all other weights) |
| **Fuel/Fuel Converger** | (not used for electric vehicles) |
| maxFuelStorKw | - | Maximum fuel storage output power in kilowatts |
| fuelStoresecsToPeakPwr | - | Seconds from 0% to 100% power output by fuel storage |
| fuelStorKwh | - | Fuel storage capacity in kilowatt hours |
| fuelStorKwhPerKg | - | Fuel storage density in watt hours per kilogram |
| maxFuelConvKw | - | Maximum output of fuel converter in kilowatts |
| fcEffMap | - | Fuel converter efficiency map (seems to override fcEffType variable |
| fcEffType | - | Fuel cell efficiency type, see `parameters.py` file variable name FC_EFF_TYPES |
| fcAbsEffImpr | - | Fuel converter absolue efficiency impr, increases efficiency of fueled engines (vehicle.py, func: load_veh) |
| fuelConvSecsToPeakPwr | - | Fuel converter time from 0% to 100% power |
| fuelConvBaseKg | - | Fuel converter base mass in kilogram |
| fuelConvkwPerKg | - |Fuel converter energy power density in kilowatts per kilogram |
| mcPwrOutPerc | - | Motor controller power output percentage, used for making the array of output power in kw from 0-100% (vehicle.py, line 259) |
| largeBaselineEff | - | Large baseline efficiency, used to make the motor controller efficiency array (vehicle.py, line 256-157) |
| smallBaselineEff | - | Small baseline efficiency used to make the motor controller efficiency array (vehicle.py, line 256-157) |
| **Motor** |  |
| modernMax | - | Modern max, seems to be the maximum efficiency possilbe (parameters.py, line 61, vehicle.py, line 246 ) |
| maxMotorKw | motor_power | Maximum motor kilowatt output |
| motorPeakEff | motor_efficiency | Peak motor efficiency  |
| motorSecsToPeakPwr | - | Seconds from 0% to 100% power output for motor |
| stopStart  | - | Stop start function enable |
| mcPeKgPerKw | - | Motor controller specific power in kilograms per kilowatt (what is Pe?) |
| mcPeBaseKg | - | Motor controller base kg (what is Pe?) |
| **ESS** |  |
| maxEssKw | - | Max energy storage system output in kilowatt |
| essKgPerKwh | - | Energy storage system energy density in kilograms per kilowatt hour |
| essBaseKg | mass (kind of) | Energy storage system base mass in kg |
| essRoundTripEff | - | Energy storage system round trip efficiency in percentage |
| essLifeCoefA | - | Energy storage system life coefficient A |
| essLifeCoefB | - | Energy storage system life coefficient B |
| **Wheels** | - |
| wheelInertiaKgM2 | rotation_inertia | Wheel inertia in kilogram * meters ^2 |
| numWheels | - | Number of wheels |
| wheelRrCoef | wheel_pressure (kind of) | Wheel rolling coefficient |
| wheelRadiusM | - | Wheel radius in meters |
| wheelCoefOfFric | - | Wheel coefficient of friction |
| **SOC, ESS Discharge/Charge** | - |
| minSoc | - | Minimum State of Charge for ESS |
| maxSoc | - | Maximum State of Charge for ESS |
| essDischgToFcMaxEffPerc | - | Maximum efficiency of ESS discharging to fuel converter |
| essChgToFcMaxEffPerc | - | Maximum efficiency of ESS charging from fuel converter |
| **Acceleration, FC, Efficiency, Mass, Regen, etc** |  |
| maxAccelBufferMph | - |  |
| maxAccelBufferPercOfUseableSoc | - |  |
| percHighAccBuf | - |  |
| mphFcOn | - | speed at which the fuel converter must be on |
| kwDemandFcOn | - | power required to turn the fuel converter on |
| altEff | - | alternator efficiency |
| chgEff | - | charging efficiency |
| auxKw | - | auxiliary load in kilowatts |
| forceAuxOnFC | - | force the fuel converter on when aux load is on (boolean) |
| transKg | mass (kind of) | transmission weight in kg |
| transEff | - | transmission efficiency |
| compMassMultiplier | - | component mass multiplier, multiplies component mass by this number (vehicle.py, func: set_veh_mass) |
| essToFuelOkError | - | ESS to fuel ok error? |
| maxRegen | - | maximum regen (assumed in kw) |
| **Val: MPGGE, KwhPM, 0 to 60, etc** | (not used, for reference) |
| valUddsMpgge | - | Udds Mpge (electric MPG) |
| valHwyMpgge  | - | Highway Mpge |
| valCombMpgge | - | Combined Mpge |
| valUddsKwhPerMile | - | Udds energy consumption in KwH per mile |
| valHwyKwhPerMile | - | Highway energy consumption in KwH per mile |
| valCombKwhPerMile | - | Combined energy consumption in KwH per mile |
| valCdRangeMi | - | cd (?) range in miles, not used so doesn't really matter |
| valConst65MphKwhPerMile | - |  energy consumption in KwH per mile at 65 mph |
| valConst60MphKwhPerMile | - | energy consumption in KwH per mile at 60 mph |
| valConst55MphKwhPerMile | - | energy consumption in KwH per mile at 55 mph |
| valConst45MphKwhPerMile | - | energy consumption in KwH per mile at 45 mph |
| valUnadjUddsKwhPerMile  | - | unadjusted udds energy usage per mile (kwh/mile) |
| valUnadjHwyKwhPerMile | - | unadjusted highway energy usage per mile (kwh/mile) |
| val0To60Mph | - | 0-60mph time |
| valEssLifeMiles | - | life of ESS in mile |
| valRangeMiles | - | range of car in miles |
| valVehBaseCost | - | base cost of vehicle (USD) |
| valMsrp | - | MSRP of vehicle (USD) |
| minFcTimeOn | - | minimum time for the fuel converter to be on |
| idleFcKw | - | idle power of fuel converter (unclear if this is used by fc or output by fc) |

# Track Variables

This simulation uses track data loaded from a designated, or default, csv file 
in the directory /tracks. 

The format of the csv file follows that of the Technical University of Munch's 
Institute for Automotive Technology's autonomous electric car racing simulation
(https://github.com/TUMFTM/global_racetrajectory_optimization). There are two 
added variables, though, for elevation and air density. 

The race trajectories in these files is created using TUM's simulation, with 
elevation added in afterward.

## Track Variable Definitions

| s_m | - | meters | Curvi-linear distance along the raceline.* |
| x_m | - | meters | X-coordinate of raceline point.* |
| y_m | - | meters | Y-coordinate of raceline point.* |
| psi_rad | - | radians | Heading of raceline in current point from -pi to pi radians. Zero is north (along y-axis).* |
| kappa_radpm | - | radians/meter | Curvature of the raceline at current point.* |
| vx_mps | - | meters/second | Target velocity at current point.* |
| ax_mps2 | - | meters/second^2 | Target acceleration at current point. Assumed to be constant.* |
| elev_m | - | meters | Elevation of the track at the corresponding s_m point. |
| air_dens | - | kilograms/meter^3 | Air density along the track. |
| *Info taken from the TUM simulation readme (https://github.com/TUMFTM/global_racetrajectory_optimization). |



