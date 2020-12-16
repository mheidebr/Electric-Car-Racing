# Electric-Car-Racing
For Electric Race Car Simulations, simulating how much 
energy it takes to race an electric car around tracks

# Usage
To use this simulation you must have python (3.X) installed on your machine
Once installed simply navigate to the top level of this repo and run `python3 simulation.py`
A UI should appear and results should be plotted, there will also be command line printout
for debugging purposes.

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
# On Ubuntu 20.04 Install the runsnake app and associated packages as follows:
$ sudo apt install runsnakerun
# Verify the installation: `which runsnake` should return something in your $PATH
$ which runsnake

# Run runsnake
# call runsnake with `profile.out` as an argument: `runsnake profile.out`
$ runsnake profile.out
# That should do it!
