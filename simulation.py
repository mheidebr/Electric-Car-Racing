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
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import cProfile
from datastore import (DataStore, RacingSimulationResults)
from logging_config import configure_logging
from physics_equations import (max_negative_power_physics_simulation,
                               max_positive_power_physics_simulation,
                               constrained_velocity_physics_simulation,
                               )
from electric_car_properties import ElectricCarProperties
from track_properties import (TrackProperties,
                              high_plains_raceway)

logger = logging.getLogger(__name__)


class MainWindow(QWidget):

    # define the SIGNALs that MainWindow will send to other threads
    mainWindowStartCalculatingSignal = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, parent=None)

        self.data_store = DataStore()
        logger.info("MainWindow: DataStore initialized",
                extra={'sim_index': self.data_store.get_simulation_index()})

        # Create GUI related resources
        self.setWindowTitle('Race Simulation')
        
        # create the user play controls and data results graphs to run the simulation
        self.createUserDisplayControls()

        # create placeholders for the plots MainWindow will delivering (updating)
        # data into.
        self.graphs = pg.GraphicsLayoutWidget(show=True, title="Race Sim plots")
        self.graphs.resize(1000, 540)
        self.p1 = self.graphs.addPlot(name="Plot1", title="Time (s)")
        self.p2 = self.graphs.addPlot(name="Plot2", title="Distance (m)")
        self.p2.hide()
        self.p3 = self.graphs.addPlot(name="Plot3", title="Velocity (m/s)")
        self.p3.hide()
        self.p4 = self.graphs.addPlot(name="Plot4", title="Acceleration (m/s^2)")
        self.p4.hide()
        self.p5 = self.graphs.addPlot(name="Plot5", title="Motor Power")
        self.p5.hide()
        self.p6 = self.graphs.addPlot(name="Plot6", title="Battery Power")
        self.p6.hide()
        self.p7 = self.graphs.addPlot(name="Plot7", title="Battery Energy (joules)")
        self.p7.hide()

        # Links user X-coordinate movements of all plots together. Practically, there has
        # to be one plot they all link to, and in this case it's self.p1 (Time) b
        self.p2.setXLink(self.p1)
        self.p3.setXLink(self.p1)
        self.p4.setXLink(self.p1)
        self.p5.setXLink(self.p1)
        self.p6.setXLink(self.p1)
        self.p7.setXLink(self.p1)

        # Layout the major GUI components
        #self.layout = QtGui.QVBoxLayout()
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.userDisplayControlsGroup)
        self.layout.addWidget(self.graphs)
        self.setLayout(self.layout)

        # Create the instances of our worker threads
        self.simulationThread = SimulationThread(self.data_store)
        self.plotRefreshTimingThread = PlotRefreshTimingThread()

        # Setup the SIGNALs to be received from the worker threads
        self.simulationThread.simulationThreadSignal.connect(self.signalRcvFromSimulationThread)
        self.plotRefreshTimingThread.plotRefreshTimingSignal.connect(self.signalPlotRefresh)

        # TODO - what mechanism and what to do when SimulationThread or dies like
        #       refresh GUI and save/close results file??
        #self.simulationThread.finished.connect(self.simulationThreadFinished)
        #self.simulationThread.terminated.connect(self.simulationThreadTerminated)

        # Now that the SimulationThread has been created (but not yet running), connect the
        # Button clicked in MainWindow - call a SimulationThread method to do something
        self.buttonRun.clicked.connect(self.createStartCalculatingSignal)
        self.buttonStop.clicked.connect(self.simulationThread.thread_stop_calculating)
        self.checkboxDistanceBreakpoint.clicked.connect(self.enableBreakpointSpinbox)

        self.simulationThread.start()
        self.plotRefreshTimingThread.start()

    def enableBreakpointSpinbox(self):
        if self.checkboxDistanceBreakpoint.isChecked() == True:
            self.spinboxDistanceBreakpoint.setEnabled(True)
            self.spinboxDistanceBreakpoint.setReadOnly(False)
        else:
            self.spinboxDistanceBreakpoint.setEnabled(False)
            self.spinboxDistanceBreakpoint.setReadOnly(True)
        
    def createStartCalculatingSignal(self):
        """
        Send a SIGNAL to the simulation thread to start the simulation calculations.
        Based on the user's control settings in the GUI, figure out what "distance" value 
        to send with the signal to Simulation Thread to start/continue simulation

        "distance" value sent to the SimulationThread is overload with these meanings:
          >0 distance in meters from the start on the track...
          =0 singlestep, 
          <0 whole track, 
        """
        if self.checkboxDistanceBreakpoint.isChecked() == True:
            distance = self.spinboxDistanceBreakpoint.value()
        else:
            # No breakpoint indicated on GUI so run the whole track or 
            # until user hits "pause" button
            distance = -1

        # signal the thread
        self.simulationThread.thread_start_calculating(distance)
        
    def createUserDisplayControls(self):
        self.labelDisplayControl = QLabel("Display Control")

        #  Note - FYI - created in the order the controls appear on screen
        self.labelStatus = QLabel("Status")
        self.textboxStatus = QLineEdit("Initialized", self)
        self.textboxStatus.setReadOnly(True)
        
        self.buttonRun = QPushButton('Run/Continue', self)
        self.buttonRun.setEnabled(True)
        self.buttonStop = QPushButton('Pause', self)
        self.buttonStop.setEnabled(True) 
        
        self.checkboxDistanceBreakpoint = QCheckBox('Distance Breakpoint (m)', self)
        self.checkboxDistanceBreakpoint.setChecked(False) 
        self.spinboxDistanceBreakpoint = QDoubleSpinBox()
        self.spinboxDistanceBreakpoint.setReadOnly(True)
        self.spinboxDistanceBreakpoint.setRange(0,999999)

        #outputs of simulation
        self.labelSimulationIndex = QLabel("Current Sim. Index")
        self.textboxSimulationIndex = QLineEdit("0",self)
        self.textboxSimulationIndex.setReadOnly(False)

        self.checkboxTime = QCheckBox('Time (s)', self)
        self.checkboxTime.setChecked(False)
        self.spinboxTime = QDoubleSpinBox()
        self.spinboxTime.setReadOnly(True)
        self.spinboxTime.setRange(0, 999999)

        self.checkboxDistance = QCheckBox('Distance (m)', self)
        self.checkboxDistance.setChecked(False) 
        self.spinboxDistance = QDoubleSpinBox()
        self.spinboxDistance.setReadOnly(True)
        self.spinboxDistance.setRange(0,999999)

        self.checkboxVelocity = QCheckBox('Velocity (m/s)', self)
        self.checkboxVelocity.setChecked(False) 
        self.spinboxVelocity = QDoubleSpinBox()
        self.spinboxVelocity.setReadOnly(True)
        self.spinboxVelocity.setRange(0,999999)

        self.checkboxAcceleration = QCheckBox('Acceleration (m/s^2)', self)
        self.checkboxAcceleration.setChecked(False) 
        self.spinboxAcceleration = QDoubleSpinBox()
        self.spinboxAcceleration.setReadOnly(True)

        self.checkboxMotorPower = QCheckBox('Motor Power', self)
        self.checkboxMotorPower.setChecked(False) 
        self.spinboxMotorPower = QDoubleSpinBox()
        self.spinboxMotorPower.setReadOnly(True)
        self.spinboxMotorPower.setRange(0,999999)

        self.checkboxBatteryPower = QCheckBox('Battery Power', self)
        self.checkboxBatteryPower.setChecked(False) 
        self.spinboxBatteryPower = QDoubleSpinBox()
        self.spinboxBatteryPower.setReadOnly(True)
        self.spinboxBatteryPower.setRange(0,999999)
        
        self.checkboxBatteryEnergy = QCheckBox('Battery Energy (j)', self)
        self.checkboxBatteryEnergy.setChecked(False) 
        self.spinboxBatteryEnergy = QDoubleSpinBox()
        self.spinboxBatteryEnergy.setReadOnly(True)
        self.spinboxBatteryEnergy.setRange(0,999999)

        #self.userDisplayControlsGroup = QtGui.QGroupBox('User Display Controls')
        self.userDisplayControlsGroup = QGroupBox('User Display Controls')
        #self.userDisplayControlsLayout= QtGui.QGridLayout()
        self.userDisplayControlsLayout= QGridLayout()
        self.userDisplayControlsLayout.addWidget(self.labelStatus,                  0, 0)
        self.userDisplayControlsLayout.addWidget(self.textboxStatus,                0, 1)
        self.userDisplayControlsLayout.addWidget(self.buttonRun,                    1, 0)
        self.userDisplayControlsLayout.addWidget(self.buttonStop,                   1, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxDistanceBreakpoint,   2, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxDistanceBreakpoint,    2, 1)
        self.userDisplayControlsLayout.addWidget(self.labelSimulationIndex,         3, 0)
        self.userDisplayControlsLayout.addWidget(self.textboxSimulationIndex,       3, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxTime,                 4, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxTime,                  4, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxDistance,             5, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxDistance,              5, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxVelocity,             6, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxVelocity,              6, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxAcceleration,         7, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxAcceleration,          7, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxMotorPower,           8, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxMotorPower,            8, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxBatteryPower,         9, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxBatteryPower,          9, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxBatteryEnergy,        10, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxBatteryEnergy,         10, 1)
        self.userDisplayControlsGroup.setLayout(self.userDisplayControlsLayout)

    def simulationThreadResultsDataDisplay(self):
        # TODO placeholder for real work to be done when the SimulationThread (a simulationThread thread)
        # SIGNALs MainWindow new data is available in shared memory
        print('Window SIGNAL from SimulationThread: Results_data_ready')

    def simulationThreadFinished(self):
        # TODO placeholder for SimulationThread SIGNALs ??exiting
        # data is available in shared memory
        print('Window: SIGNAL From SimulationThread: Finished')

    def simulationThreadTerminated(self):
        # TODO placeholder for SimulationThread SIGNALs terminated
        print('Window: SIGNAL From SimulationThread: Terminated')

    """
    Slots routines to handle SIGNALs sent to MainWindow from other threads
    """
    @pyqtSlot(str)
    def signalRcvFromSimulationThread(self, text):
        #self.buttonRun.setText(text)
        self.textboxStatus.setText(text)

    @pyqtSlot()
    def signalPlotRefresh(self):
        #Display/update the window to display computation status, data, and plots selected by the user
        # This is called periodically because of the signal emitted from PlotRefreshTimingThread
        current_sim_index = (self.data_store.get_simulation_index())
        logger.info("MainWindow:", extra={'sim_index': current_sim_index})
        self.textboxSimulationIndex.setText("{}".format(current_sim_index))
        
        """
        Only refresh data if the simulations calculations have begun, indicated by 
        current_sim-index > 0
        Note: current_sim_index is descremented "-1" for the following calls
        because the lap_velocity_simulation calculations may be incomplete for the index
        when this "plot" signal was received and interrupted it. That is, the 
        SimulationThread is/could be still updating a DataStore data (lists) records  
        simulation_index and not all lists # have been calculated, so we should 
        just plot upto the last complete record.
        """
        if current_sim_index > 0 :
            
            # Get the current data values and update the corresponding display field textbox
            time = self.data_store.get_time_at_index(current_sim_index-1)
            self.spinboxTime.setValue(time)
            
            distance = self.data_store.get_distance_at_index(current_sim_index-1)
            self.spinboxDistance.setValue(distance)
            
            velocity = self.data_store.get_velocity_at_index(current_sim_index-1)
            self.spinboxVelocity.setValue(velocity)
            
            acceleration = self.data_store.get_acceleration_at_index(current_sim_index-1)
            self.spinboxAcceleration.setValue(acceleration)
            
            motor_power = self.data_store.get_motor_power_at_index(current_sim_index-1)
            self.spinboxMotorPower.setValue(motor_power)
            
            battery_power = self.data_store.get_battery_power_at_index(current_sim_index-1)
            self.spinboxBatteryPower.setValue(battery_power)
            # TBD not yet implemented in physics_equations
            #battery_energy = self.data_store.get_battery_energy_at_index(current_sim_index-1)
            #self.spinboxBatteryEnergy.setValue(battery_energy)
            
            # Display the data values
            
            # create a new plot for every point simulated so far
            x = [z for z in range(current_sim_index)]
            _time = []
            _distance = []
            _velocity = []
            _max_velocity = []
            _acceleration = []
            _motor_power = []
            _battery_power = []
            _battery_energy = []
            
            _time = self.data_store.get_time_list(current_sim_index)
            _distance = self.data_store.get_distance_list(current_sim_index)
            _velocity = self.data_store.get_velocity_list(current_sim_index)
            _max_velocity = self.data_store.get_track_max_velocity_list(current_sim_index)
            _acceleration = self.data_store.get_acceleration_list(current_sim_index)
            _motor_power = self.data_store.get_motor_power_list(current_sim_index)
            _battery_power = self.data_store.get_battery_power_list(current_sim_index)
            #TODO not yet implemented
            #_battery_energy = self.data_store.get_battery_energy_list(current_sim_index)
            
            self.p1.plot(x=x, y=_time, name="Plot1", title="Time")        
            
            # selectively display the plots based on the checkboxes 
            if self.checkboxDistance.isChecked() == True :
                self.p2.show()
                self.p2.plot(x=x, y=_distance, name="Plot2", title="Distance (m)")        
            else:
                self.p2.hide()
                
            if self.checkboxVelocity.isChecked() == True :
                self.p3.show()
                self.p3.plot(x=x, y=_max_velocity, name="Plot3", title="Max Velocity (m/sec)", pen='r')
                self.p3.plot(x=x, y=_velocity, name="Plot3", title="Velocity (m/sec)")        
                
            else:
                self.p3.hide()
                
            if self.checkboxAcceleration.isChecked() == True :
                self.p4.show()
                self.p4.plot(x=x, y=_acceleration, name="Plot4", title="Acceleration (m/sec^2)")        
            else:
                self.p4.hide()
                
            if self.checkboxMotorPower.isChecked() == True :
                self.p5.show()
                self.p5.plot(x=x, y=_motor_power, name="Plot5", title="Motor Power")        
            else:
                self.p5.hide()
                
            if self.checkboxBatteryPower.isChecked() == True :
                self.p6.show()
                self.p6.plot(x=x, y=_battery_power, name="Plot6", title="Battery Power")        
            else:
                self.p6.hide()
                
            """TBD - to be added once Battery Energy is working in physics_equations
            if self.checkboxBatteryEnergy.isChecked() == True :
                self.p7.show()
                self.p7.plot(x=x, y=_battery_energy, name="Plot7", title="Battery Energy (joules)")        
            else:
                self.p7.hide()
            """

class SimulationThread(QThread):
    # Define the Signals we'll be emitting to the MainWindow
    simulationThreadSignal = pyqtSignal(str)
    simulationThreadPlotSignal = pyqtSignal(int)
    breakpointDistance = 0

    def __init__(self, passed_data_store, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.setObjectName("SimulationThread")

        """ SimulationComputing is used for staring/stopping loop control logic which is
        controlled ( signalled) from the MainWindow.
        Start without compution in the simulationThread running
        """
        self.simulationComputing = False
        self.breakpointDistance = 0

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
        wheel_pressure_bar = 3 # bar

        track = TrackProperties()
        track.set_air_density(air_density)

        for distance in high_plains_raceway:
            track.add_critical_point(distance, high_plains_raceway[distance], track.FREE_ACCELERATION)
        track.generate_track_list(segment_distance)

        car = ElectricCarProperties()
        car.set_car_parameters(mass=mass, rotational_inertia=rotational_inertia,
                               motor_power=battery_power, motor_efficiency=motor_efficiency,
                               battery_capacity=10, drag_coefficient=drag_coefficient,
                               frontal_area=frontal_area, wheel_radius=wheel_radius,
                               wheel_pressure_bar=wheel_pressure_bar)

        self._data_store.initialize_lap_lists(len(track.distance_list))
        self._data_store.set_car_properties(car)
        self._data_store.set_track_properties(track)

    """ SimulationThread signal handling routines. This is the collection of SLOTS
        that get signaled (emitted) from the MainWindow and tell the SimulationThread 
        what to do, like change states and start calculating, pause, etc.
    """
    @pyqtSlot()
    def thread_start_calculating(self, distance_value):
        """
         This signal (slot) handler takes the distance value 
         and updates SimulationThread computing state and interprets
         the distance_value into appropriate values for "breakpoints" to, 
         if necessary, to stop computing. 
        """
        print("Breakpoint Distance value:{}".format(distance_value))
        logger.info('Slot:thread_start_calculating :', 
                extra={'sim_index': self._data_store.get_simulation_index()})

        if distance_value == 0:
            logger.info('Slot:thread_start_calculating SINGLE STEP NOT IMPLEMENTED:', 
                extra={'sim_index': self._data_store.get_simulation_index()})
                #TODO - finish this breakpoint case
            self.simulationComputing = False

        elif distance_value == -1:
            logger.info('Slot:thread_start_calculating RUN TO COMPLETION :', 
                extra={'sim_index': self._data_store.get_simulation_index()})
            # set the breakpoint to be a very large number to indicate run to completion
            self.breakpointDistance = 9999999
            self.simulationComputing = True
        else:
            # run to the distance value point in the track
            sim_index = self._data_store.get_simulation_index()
            if distance_value > self._data_store.get_distance_at_index(sim_index) :
                logger.info('Slot:thread_start_calculating RUN TO DISTANCE :', 
                    extra={'sim_index': sim_index})
                # requested breakpoint is further down the track
                self.breakpointDistance = distance_value
                # Start computing and acknowledge to MainWindow by sending a signal back 
                self.simulationThreadSignal.emit("Calculating...")
                # "state" variable indicating thread should be calculating
                self.simulationComputing = True
            else:
                logger.info('Slot:thread_start_calculating PAST REQUESTED DISTANCE :', 
                    extra={'sim_index': sim_index})
                # simulation has already past this point in the track, don't proceed
                self.simulationComputing = False

    @pyqtSlot()
    def thread_stop_calculating(self):
        logger.info('Slot:thread_stop_calculating :', 
                extra={'sim_index': self._data_store.get_simulation_index()})
        # Now send a signal back to the main window
        self.simulationThreadSignal.emit("Paused")

        # "state" variable indicating thread should stop calculating
        self.simulationComputing = False

    def racing_simulation(self):
        """Function accepts a car and a track and executes
        a simulation to ouput critical metrics related
        to battery life and track speed.

        Args:
            Nothing, all required vars are defined in class

        Returns:
            Nothing, all required vars are defined in class

        """
        results = RacingSimulationResults()

        self.lap_velocity_simulation()
        # only calculate results if the simulation ran through without an interruption
        if not self._data_store.exit_event.is_set():
            lap_results = self._data_store.get_lap_results()

            # TODO fix this
            #results.laps_per_pit_stop = car["battery_capacity"] / lap_results.motor_energy_list[-1]
            results.lap_time = lap_results.end_velocity
            results.lap_results = lap_results
            self._data_store.set_race_results(results)

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
        add_physics_result_to_datastore = self._data_store.add_physics_results_to_lap_results
        get_velocity = self._data_store.get_velocity_at_index

        track = self._data_store.get_track_properties()
        air_density = track.get_air_density()
        car = self._data_store.get_car_properties()

        # need to populate the time profile be the same length as the distance list
        # to complete a lap of simulation
        list_len = len(track.distance_list)
        logger.debug('track.distance_list length={}'.format(list_len), 
                extra={'sim_index': self._data_store.get_simulation_index()})

        # TODO - Add self.simulationComputing to loop control to while
        while self._data_store.get_simulation_index() < list_len:

            # get the new index we are going to calculate
            sim_index = self._data_store.get_simulation_index()

            if self._data_store.exit_event.is_set():
                break
            distance_of_travel = (track.distance_list[sim_index] -
                                  track.distance_list[sim_index - 1])

            
            # only continue simulation computing if the GUI says to do so.
            if (self.simulationComputing == True and self.breakpointDistance > track.distance_list[sim_index]): 
                velocity = get_velocity(sim_index - 1)
                physics_results = max_positive_power_physics_simulation(velocity,
                                                                        distance_of_travel,
                                                                        car,
                                                                        air_density)
                add_physics_result_to_datastore(physics_results, sim_index)
                # check if velocity constraints are violated
                if get_velocity(sim_index) > track.max_velocity_list[sim_index]:
                    # velocity constraint violated!!
                    # start walking back until velocity constraint at sim_index is met
                    logger.info("velocity constraint violated starting walk back, current v: {}, max: {}"
                                .format(physics_results.final_velocity, track.max_velocity_list[sim_index]),
                                extra={'sim_index': self._data_store.get_simulation_index()})
                    max_velocity_constraint = track.max_velocity_list[sim_index]
                    while get_velocity(sim_index) > max_velocity_constraint:
                        """This while loop's purpose is to recalculate a portion of the
                        car's car profile because the car ended up going too fast at a point on the
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
                            add_physics_result_to_datastore(physics_results, i)

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
                            add_physics_result_to_datastore(physics_results, sim_index)
                        #end of while while get_velocity(sim_index) > max_velocity_constraint:

                    
                    # walk back complete, reset walk back index for next time
                    self._data_store.reset_walk_back_counter()

                # completed calculation for the latest simulation index,
                self._data_store.increment_simulation_index()
            else:
                # self.simulationComputing is False or we've reached a breakpoint, 
                # so wait for GUI user to indicate proceed
                
                if self.simulationComputing == True :
                    # if we're computing and got here, we must have hit a breakpoint, therefore pause
                    # Now send a signal back to the main window
                    self.simulationThreadSignal.emit("Paused")
                    
                    # "state" variable indicating thread should stop calculating
                    self.simulationComputing = False
                    
                #else: 
                    # we've began not computing or a breakpoint already has sent us there
                    # so do nothing more than waitk
                
                # in any case, wait until user gives us a new condition to continue computing
                time.sleep(1.0)
                logger.debug("waiting for simulationComputing==True",
                        extra={'sim_index': sim_index})
        # end of while data_store.get_simulation_index() < list_len:

        logger.info("SIMULATION COMPLETE!", extra={'sim_index': 'N/A'})
        self.simulationThreadSignal.emit("Finished!")
        self._data_store.exit_event.set()

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment with the thread's start() method has been setup,
        # and then runs "continuously"
        logger.info("SimulationThread: entering cProfile.runctx() ",
                extra={'sim_index': 'N/A'})

        # profiling tool, look at results with runsnake:
        # https://kupczynski.info/2015/01/16/profiling-python-scripts.html
        # this has relatively little overhead for the overall runtime of the program
        # I have only been able to get the runsnake files to work on linux
        # alternative profile results viewer for windows (untried): https://sourceforge.net/projects/qcachegrindwin/
        cProfile.runctx("self.racing_simulation()", globals(), locals(), 'profile-simulation.out')
        
class PlotRefreshTimingThread(QThread): 
    # Thread responsible for a periodic signal to the MainWindow which when received causes 
    # MainWindow to refresh it's plots.

    # Define the Signals we'll be emitting to the MainWindow
    plotRefreshTimingSignal = pyqtSignal()

    # start without compution in the simulationThread running

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False

        logger.info("PlotRefreshTimingThread: __init()__",
                extra={'sim_index': 'N/A'})

        # TODO connect some signals from the main window to us
        #self.connect(self, QtCore.SIGNAL('To_End',self.processToEnd)


    def __del__(self):    
        # Before a PlotRefreshTimingThread object is destroyed, we need to ensure that it stops 
        # processing.  For this reason, we implement the following method in a way that 
        # indicates to  the part of the object that performs the processing that it must stop,
        # and waits until it does so.
        self.exiting = True
        self.wait()

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment with the thread's start() method has been setup,
        # and then runs "continuously" to do the work of the thread as it's main
        # processing loop

        logger.info("PlotRefreshTimingThread: entering while() ",
                extra={'sim_index': 'N/A'})
        while True:
            time.sleep(5.0)
            self.plotRefreshTimingSignal.emit()


if __name__ == "__main__":
    MainApp = QApplication(sys.argv)
    if __name__ == "__main__":
        configure_logging()
    window = MainWindow()
    window.show()
    sys.exit(cProfile.runctx("MainApp.exec_()", globals(), locals(), 'profile-display.out'))
    
