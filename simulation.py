# The actual simulation goes here
# This is the main application framework for the Race Simulation which contains the MainWindow,
# based on PyQt, and spawns a Qthread SimulationThread thread.  Qt signals/slots are used to 
# communicate in both directions between them to control (start/pause/stop) and report results 
# between them. 
#
# 
# To Execute: python3 simulation.py
#
# Dependencies: python3, PyQt5 etc.
#
# Description: MainWindow is created by the app, which in turn starts a SimulationThread thread. o
# Note: the MainWindow is not a QMainWindow, rather a QWidget which allows for more flexibility
# in placing controls, plots, etc. 
# The MainWindow contains user controls such push button (QPushButton) that when pressed, 
# emits a signal that is captured  but the "slot" on the SimulationThread thread which acts on it 
# (thread_start_calculating). 
# Likewise, the SimulationThread thread emits various signals which are captured by associated slots 
# in the MainWindow and acted upon. 
# In either direction data (e.g. input parameters to the SimulationThread thread or results of 
# calculation from the SimulationThread thread) passed with emitted signal is then displayed on the 
# PushButton. 
# 
# This is based on : 
# https://stackoverflow.com/questions/52993677/how-do-i-setup-signals-and-slots-in-pyqt-with-qthreads-in-both-directions
# Author: RMH 10/28/2020
#
# Status:
# 11/25/20 This version does NO simulating and provides only the very basic GUI framework 
# with a simple placeholder graph/plot, threading, and signalling  between the thread and 
# the main window.
# 12/1/20 Adding a data storage area to share between the SimulationThread and MainWindow thread
# which incorporates a mutex mechanism (QReadWriteLock) to allow coordinating sharing of the
# data which MainWindow will be consuming (reading).
# 12/52/20 Manual merge in branch 'one-lock-rules-them-all' simulation code with the QThread
# architecture framed in from the previous versions of this branch

# USE ONLY SI UNITS
import sys
import time
import logging
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import cProfile
from datastore import (DataStore, RacingSimulationResults)
from logging_config import configure_logging
from physics_equations import (max_negative_power_physics_simulation,
                               max_positive_power_physics_simulation,
                               constrained_velocity_physics_simulation,
                               )
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties
from logging_config import configure_logging

logger = logging.getLogger(__name__)



class MainWindow(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, parent = None)
        print('Window: __init__')

        self.data_store = DataStore()
        print("MainWindow: Simulation Index = {}".format(self.data_store.get_simulation_index()))
        #self.data_store.increment_simulation_index()
        #print("MainWindow: Simulation Index = {}".format(self.data_store.get_simulation_index()))

        # Create GUI related resources
        self.setWindowTitle('Race Simulation')
        # create the user controls to run the simulation
        self.createControls()

        # create placeholder for the plots the SimulationThread will delivering 
        # data into.
        self.graphs = pg.GraphicsLayoutWidget(show=True, title="Race Sim plots")
        self.graphs.resize(1000,540)
        self.p1 = self.graphs.addPlot(name="Plot1", title="Velocity")        
        self.p2 = self.graphs.addPlot(name="Plot1", title="Distance")        
        self.p3 = self.graphs.addPlot(name="Plot1", title="Battery Power")        
        self.p2.setXLink(self.p1)
        #self.p2.setYLink(self.p1)
        self.p3.setXLink(self.p1)
        #self.p3.setYLink(self.p1)
        
        # Layout the major GUI components 
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.graphs)
        self.layout.addWidget(self.controlsGroup)
        self.setLayout(self.layout)
        
        # Create the instances of our worker threads
        self.simulationThread = SimulationThread(self.data_store)
        self.plotRefreshThread = PlotRefreshThread()

        # Setup the SIGNALs to be received from the worker threads 
        self.simulationThread.simulationThreadSignal.connect(self.signalRcvFromSimulationThread)
        self.plotRefreshThread.plotRefreshSignal.connect(self.signalPlotRefresh)

        # TBD - what mechanism and what to do when SimulationThread or dies like
        #       refresh GUI and save/close results file??
        #self.simulationThread.finished.connect(self.simulationThreadFinished)
        #self.simulationThread.terminated.connect(self.simulationThreadTerminated)


        #Now that the SimulationThread has been created (but not yet running), connect the
        # Button clicked in MainWindow - call a SimulationThread method to do something
        self.buttonRun.clicked.connect(self.simulationThread.thread_start_calculating)
        self.buttonStop.clicked.connect(self.simulationThread.thread_stop_calculating)
        
        self.simulationThread.start()
        self.plotRefreshThread.start()
        
    def createControls(self):
        self.labelStatus = QLabel("Status")
        self.textboxStatus = QLineEdit("Initialized",self)
        self.textboxStatus.setReadOnly(True)
        self.buttonRun = QPushButton('Run/Continue', self)
        self.buttonRun.setEnabled(True) 
        self.buttonStop = QPushButton('Pause', self)
        self.buttonStop.setEnabled(True) 
        
        #a spacer to add visual space at the bottom of the gui (not used yet)
        #controlVerticalSpacer = QtGui.QSpacerItem(40,20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.controlsGroup = QtGui.QGroupBox('Controls')
        self.controlsLayout= QtGui.QGridLayout()
        self.controlsLayout.addWidget(self.labelStatus,     0, 1)
        self.controlsLayout.addWidget(self.textboxStatus,   0, 2)
        self.controlsLayout.addWidget(self.buttonRun,       0, 3)
        self.controlsLayout.addWidget(self.buttonStop,      0, 4)
        #self.controlsLayout.addItem(controlVerticalSpacer, 0, 3,QtCore.Qt.AlignTop)
        self.controlsGroup.setLayout(self.controlsLayout)
        

    def simulationThreadResultsDataDisplay(self):
        # TBD placeholder for real work to be done when the SimulationThread (a simulationThread thread)
        # SIGNALs MainWindow new data is available in shared memory
        print('Window SIGNAL from SimulationThread: Results_data_ready') 

    
    def simulationThreadFinished(self):
        # TBD placeholder for SimulationThread SIGNALs ??exiting
        # data is available in shared memory
        print('Window: SIGNAL From SimulationThread: Finished') 

    def simulationThreadTerminated(self):
        # TBD placeholder for SimulationThread SIGNALs terminated
        print('Window: SIGNAL From SimulationThread: Terminated') 

    ###################################
    #TBD REMOVE/REPLACE FOR THE SIM APP
    @pyqtSlot(str)
    def signalRcvFromSimulationThread(self, text ):
        #self.buttonRun.setText(text)
        self.textboxStatus.setText(text)

        
    @pyqtSlot()
    def signalPlotRefresh(self):
        index = self.data_store.get_simulation_index()
        print("MainWindow:signalPlotRefresh Simulation Index = {}".format(index))
        # create a new plot for every point simulated so far
        x = [z+1 for z in range(self.data_store.get_simulation_index())]
        _velocity = []
        _distance = []
        _battery_power = []
        for z in x:
            _velocity.append(self.data_store.get_velocity_at_index(z))
            _distance.append(self.data_store.get_distance_at_index(z))
            _battery_power.append(self.data_store.get_battery_power_at_index(z))
        self.curve = self.p1.plot(x=x, y=_velocity, name="Plot1", title="Velocity")        
        self.curve = self.p2.plot(x=x, y=_distance, name="Plot1", title="Distance")        
        self.curve = self.p3.plot(x=x, y=_battery_power, name="Plot1", title="Battery Power")        


class SimulationThread(QThread):
    # Define the Signals we'll be emitting to the MainWindow
    simulationThreadSignal = pyqtSignal(str)
    simulationThreadPlotSignal = pyqtSignal(int)
    

    def __init__(self, passed_data_store, parent = None):
        QThread.__init__(self, parent)
        self.exiting = False

        """ SimulationComputing is used for staring/stopping loop control logic which is 
        controlled ( signalled) from the MainWindow.
        Start without compution in the simulationThread running
        """
        self.simulationComputing = False
        self.iterations = 0

        # Initialize the simulation universe
        self._data_store = passed_data_store
        self.initialize_race()

        #print('SimulationThread: __init()__')
        #print("SimulationThread: Simulation Index = {}".format(self._data_store.get_simulation_index()))

        #connect some signals from the main window to us
        #self.connect(self, QtCore.SIGNAL('To_End',self.processToEnd)


    def __del__(self):    
        # Before a SimulationThread object is destroyed, we need to ensure that it stops processing. 
        # For this reason, we implement the following method in a way that indicates to 
        # the part of the object that performs the processing that it must stop, and waits 
        # until it does so.
        self.exiting = True
        self.wait()

        # rotational inertia estimation: http://www.hpwizard.com/rotational-inertia.html
    def initialize_race(self):

        segment_distance = 0.005  # meters, this must be very very small
        battery_power = 40000  # 40kW
        motor_efficiency = 0.8
        wheel_radius = 0.25  # m, ~20 in OD on tires
        rotational_inertia = 10  # kg*m^2
        mass = 1000  # kg
        drag_coefficient = 0.4
        frontal_area = 7  # m^2
        air_density = 1  # kg/m^3

        track = TrackProperties()
        track.set_air_density(air_density)

        track.add_critical_point(0.0, 10.0, track.FREE_ACCELERATION)
        track.add_critical_point(5.0, 5.0, track.FREE_ACCELERATION)
        track.add_critical_point(10.0, 10.0, track.FREE_ACCELERATION)
        track.add_critical_point(12.0, 25.0, track.FREE_ACCELERATION)
        track.add_critical_point(16.0, 55.0, track.FREE_ACCELERATION)
        track.add_critical_point(50.0, 80.0, track.FREE_ACCELERATION)
        track.generate_track_list(segment_distance)

        car = ElectricCarProperties()
        car.set_car_parameters(mass=mass, rotational_inertia=rotational_inertia,
                               motor_power=battery_power, motor_efficiency=motor_efficiency,
                               battery_capacity=10, drag_coefficient=drag_coefficient,
                               frontal_area=frontal_area, wheel_radius=wheel_radius)

        self._data_store.initialize_lap_lists(len(track.distance_list))
        self._data_store.set_car_properties(car)
        self._data_store.set_track_properties(track)

    """ SimulationThread signal handling routines. This is the collection of SLOTS
        that get signaled from the MainWindow tell the SimulationThread what to do, 
        like change states and start calculating, pause, etc.
    """
    @pyqtSlot()
    def thread_start_calculating( self ):
        print('Slot:thread_start_calculating :',QThread.currentThread())
        import time
        #Now send a signal back to the main window
        self.simulationThreadSignal.emit("Calculating...")
        # "state" variable indicating thread should be calculating
        self.simulationComputing = True

    @pyqtSlot()
    def thread_stop_calculating( self ):
        print('Slot:thread_stop_calculating :',QThread.currentThread())
        #Now send a signal back to the main window
        self.simulationThreadSignal.emit("Paused")
        
        # "state" variable indicating thread should stop calculating
        self.simulationComputing = False

    # TBD!!! remove data_store parameter and fix data_store references to use self._data_store
    def racing_simulation(self):
        """Function accepts a car and a track and executes
        a simulation to ouput critical metrics related
        to battery life and track speed.

        Args:
            data_store (DataStore): Thread safe storage for all simulation data

        Returns:
            Nothing (all data saved in the datastore)

        """
        results = RacingSimulationResults()

        self.lap_velocity_simulation()
        # only calculate results if the simulation ran through without an interruption
        if not self._data_store.exit_event.is_set():
            lap_results = self._data_store.get_lap_results()
            car = self._data_store.get_car_properties()

            index = self._data_store.get_simulation_index()
            #print('sim_index {} lap_results {}'.format(index, lap_results.motor_energy_list))

            # TBD fix this 
            #results.laps_per_pit_stop = car["battery_capacity"] / lap_results.motor_energy_list[-1]
            results.lap_time = lap_results.end_velocity
            results.lap_results = lap_results
            self._data_store.set_race_results(results)


    # TBD!!! remove data_store parameter and fix data_store references to use self._data_store
    def lap_velocity_simulation(self):
        """Function calculates the velocity profile of a car with
        car_properties on a track with track_properties. The car
        starts with an ititial velocity of initial_velocity.

        Args:
            data_store (DataStore): Thread safe storage for all simulation data

        Returns:
            Nothing (all data saved in the datastore)
        """
        # performance increases by assigning local functions
        # https://towardsdatascience.com/10-techniques-to-speed-up-python-runtime-95e213e925dc
        add_pys_result_to_datastore = self._data_store.add_physics_results_to_lap_results
        get_velocity = self._data_store.get_velocity_at_index

        track = self._data_store.get_track_properties()
        air_density = track.get_air_density()
        car = self._data_store.get_car_properties()

        sim_index = self._data_store.get_simulation_index()
        # need to populate the time profile be the same length as the distance list
        # to complete a lap of simulation
        list_len = len(track.distance_list)
        print('lap_velocity_simulation: list_len={}'.format(list_len))

        #TBD - Add self.simulationComputing to loop control to while
        while self._data_store.get_simulation_index() < list_len:
            sim_index = self._data_store.get_simulation_index()
            #print('lap_velocity_simulation: simulation_index={}'.format(sim_index))

            # only continue simulation if the GUI says to do so.
            if (self.simulationComputing == True):
                if self._data_store.exit_event.is_set():
                    break
                #sim_index = self._data_store.get_simulation_index()
                distance_of_travel = (track.distance_list[sim_index] -
                                      track.distance_list[sim_index - 1])

                velocity = get_velocity(sim_index - 1)
                physics_results = max_positive_power_physics_simulation(velocity,
                                                                        distance_of_travel,
                                                                        car,
                                                                        air_density)
                add_pys_result_to_datastore(physics_results, sim_index)
                # check if velocity constraints are violated
                if get_velocity(sim_index) > track.max_velocity_list[sim_index]:
                    # velocity constraint violated!!
                    # start walking back until velocity constraint at sim_index is met
                    logger.info("velocity constraint violated starting walk back, current v: {}, max: {}"
                                .format(physics_results.final_velocity, track.max_velocity_list[sim_index]),
                                extra={'sim_index': self._data_store.get_simulation_index()})
                    max_velocity_constraint = track.max_velocity_list[sim_index]
                    while get_velocity(sim_index) > max_velocity_constraint:
                        """This while loop's pupose is to recalculate a portion of the
                        car's car profile because the car ended up going to fast at a point on the
                        track. To recalculate the following happens:

                        1. a "walk back" index is used to track how far back the recalculation occurs
                        2. from the index (sim_index - walk_back_index) to (sim_index - 1) the results
                           are calculated as a maximum regeneration effort by the motor
                        3. at the sim_index the results are calculated as a constrained velocity
                            - if the results of the calculation are realistic then the walk back is done
                            - if the results are not realistic then increment the
                              walk back counter and recalculate
                        """
                        walk_back_counter = self._data_store.get_walk_back_counter()
                        recalculation_start_index = sim_index - walk_back_counter
                        logger.debug("starting and ending walkback index: {}, {}"
                                     .format(recalculation_start_index, sim_index),
                                     extra={'sim_index': self._data_store.get_simulation_index()})
                        for i in range(recalculation_start_index, sim_index):

                            velocity = get_velocity(i - 1)
                            logger.debug("velocity: {}"
                                         .format(velocity),
                                         extra={'sim_index': i})
                            # recalculate with negative motor power
                            physics_results = max_negative_power_physics_simulation(velocity,
                                                                                    distance_of_travel,
                                                                                    car,
                                                                                    air_density)
                            logger.debug("next velocity: {}"
                                         .format(physics_results.final_velocity),
                                         extra={'sim_index': i})
                            add_pys_result_to_datastore(physics_results, i)

                        velocity = get_velocity(sim_index - 1)
                        # last deceleration will be a constrained velocity because
                        # it will be neither max positive or negative motor power
                        physics_results = \
                            constrained_velocity_physics_simulation(velocity,
                                                                    max_velocity_constraint,
                                                                    distance_of_travel,
                                                                    car,
                                                                    air_density)
                        logger.debug("velocity start, end, max: {} {} {}"
                                     .format(velocity,
                                             physics_results.final_velocity,
                                             max_velocity_constraint),
                                     extra={'sim_index': sim_index})
                        # check if constrained velocity calculation is realistic
                        # TODO other checks here can be on acceleration or wheel force
                        if physics_results.motor_power < -car["motor_power"]:
                            logger.debug(
                                "velocity constraint still violated, calculated power: {}, max power: {}"
                                .format(physics_results.motor_power, car["motor_power"]),
                                extra={'sim_index': sim_index})
                            logger.debug("sim_index, walkback: {} {}, incrementing walk back"
                                         .format(sim_index, walk_back_counter),
                                         extra={'sim_index': sim_index})
                            self._data_store.increment_walk_back_counter()
                        else:
                            logger.info(
                                "velocity constraint accepted, calculated power: {}, max power: {}"
                                .format(physics_results.motor_power, car["motor_power"]),
                                extra={'sim_index': sim_index})
                            logger.info("constrained velocity equation accepted",
                                        extra={'sim_index': sim_index})
                            add_pys_result_to_datastore(physics_results, sim_index)

                    # reset walk back index
                    self._data_store.reset_walk_back_counter()

                self._data_store.increment_simulation_index()
            else:
                # self.simulationComputing is False, so wait for GUI user to indicate proceed
                time.sleep(1)
                print('lap_velocity_simulation: waiting for simulationComputing==True')
        # end of while data_store.get_simulation_index() < list_len:

        print('lap_velocity_simultation: COMPLETE!')
        self.simulationThreadSignal.emit("Finished!")
        self._data_store.exit_event.set()


    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment with the thread's start() method has been setup, 
        # and then runs "continuously"
        print('SimulationThread: entering cProfile.runctx() ')

        # profiling tool, look at results with runsnake:
        # https://kupczynski.info/2015/01/16/profiling-python-scripts.html
        # this has relatively little overhead for the overall runtime of the program
        #cProfile.runctx("racing_simulation(self._data_store)", globals(), locals(), 'profile.out')
        cProfile.runctx("self.racing_simulation()", globals(), locals(), 'profile.out')


    """
    def run(self):        
        # to do the work of the thread as the main processing loop
        # The boolean "state" variable simulationComputing is used to control 
        # calculating should proceed in the simulation 

        #print('SimulationThread: entering while() ')
        while True:
            # TBD We need to put the bulk of the work for Race Sim here
            # with a state machine to run/pause/continue/step through calcs
            print("SimulationThread:  running")
            time.sleep(1)
            if self.simulationComputing == True:
                # The placeholder where the simulation should be doing the work 
                #cProfile.runctx("racing_simulation(self._data_store)", globals(), locals(), 'profile.out')


                self.simulationThreadSignal.emit('%x' % (self.iterations) )
                self.iterations+=1
                #self.simulationThreadPlotSignal.emit((self.data_store.get_simulation_index) )
                #self.data_store.increment_simulation_index()
                self.simulationThreadPlotSignal.emit((self._data_store.get_simulation_index()) )
                self._data_store.increment_simulation_index()
                
    """
    
class PlotRefreshThread(QThread): 
    # Thread responsible for a periodic signal to the MainWindow which when received causes 
    # it to refresh it's plots.

    # Define the Signals we'll be emitting to the MainWindow 
    plotRefreshSignal = pyqtSignal()
    
    # start without compution in the simulationThread running

    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.exiting = False

        print('PlotRefreshThread: __init()__')

        #connect some signals from the main window to us
        #self.connect(self, QtCore.SIGNAL('To_End',self.processToEnd)


    def __del__(self):    
        # Before a PlotRefreshThread object is destroyed, we need to ensure that it stops 
        # processing.  For this reason, we implement the following method in a way that 
        # indicates to  the part of the object that performs the processing that it must stop,             # and waits until it does so.
        self.exiting = True
        self.wait()

    def run(self):        
        # Note: This is never called directly. It is called by Qt once the
        # thread environment with the thread's start() method has been setup, 
        # and then runs "continuously" to do the work of the thread as it's main 
        # processing loop 

        print('PlotRefreshThread: entering while() ')
        while True:
            #print("PlotRefreshThread: running")
            time.sleep(1)
            self.plotRefreshSignal.emit()



if __name__ == "__main__":
    MainApp = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(MainApp.exec_())
