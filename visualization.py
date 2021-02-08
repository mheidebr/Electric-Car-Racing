# This is the main application Window & framework for the Race Simulation which contains the
# MainWindow, based on PyQt, and spawns a Qthread SimulationThread thread.  Qt signals/slots
# are used to communicate in both directions between them to control (start/pause/stop) and
# report results between them.
#
#
# To Execute: python3 visualization.py [-l on|off]
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

# USE ONLY SI UNITS
import sys
import time
import logging
from project_argparser import *
from PyQt5.QtCore import (QTimer, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton)
from PyQt5.QtWidgets import (QApplication, QGridLayout, QGroupBox, QDoubleSpinBox)
import pyqtgraph as pg
import cProfile
from datastore import (DataStore)
from logging_config import configure_logging
from simulation import SimulationThread


class MainWindow(QWidget):

    # define the SIGNALs that MainWindow will send to other threads
    mainWindowStartCalculatingSignal = pyqtSignal(int)

    def __init__(self, data_store, simulationThread, logger, *args, **kwargs):
        QWidget.__init__(self, parent=None)

        self.data_store = data_store
        self.simulationThread = simulationThread
        self.logger = logger

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
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.userDisplayControlsGroup)
        self.layout.addWidget(self.graphs)
        self.setLayout(self.layout)

        # Initialize private data arrays that will collect data from the simulation thread's
        # shared via data_store

        self.last_plotted_index = 0
        self._X = [0]   # our private x values for x-axis plotting
        self._time = [0]
        self._distance = [0]
        self._velocity = [0]
        self._max_velocity = [0]
        self._acceleration = [0]
        self._motor_power = [0]
        self._battery_power = [0]
        self._battery_energy = [0]
        self.time_data_line = self.p1.plot(x=self._X, y=self._time,
                                           name="Plot1", title="Time (s)")
        self.distance_data_line = self.p2.plot(x=self._X, y=self._distance,
                                               name="Plot2", title="Distance (m)")
        self.velocity_data_line = self.p3.plot(x=self._X, y=self._velocity,
                                               name="Plot3", title="Velocity (m/s)")
        self.max_velocity_data_line = self.p3.plot(x=self._X, y=self._max_velocity,
                                                   name="Plot3", title="Max Velocity (m/sec)",
                                                   pen='r')
        self.acceleration_data_line = self.p4.plot(x=self._X, y=self._acceleration,
                                                   name="Plot4", title="Acceleration (m/sec^2)")
        self.motor_power_data_line = self.p5.plot(x=self._X, y=self._motor_power,
                                                  name="Plot5", title="Motor Power")
        self.battery_power_data_line = self.p6.plot(x=self._X, y=self._battery_power,
                                                    name="Plot6", title="Battery Power")
        self.battery_energy_data_line = self.p7.plot(x=self._X, y=self._battery_energy,
                                                     name="Plot7", title="Battery Energy")

        # Setup the SIGNALs to be received from the worker threads
        self.simulationThread.simulationThreadSignal.connect(self.signalRcvFromSimulationThread)
        # self.simulationThread.simulationThreadWalkBackCompleteSignal.connect(self.signalWalkBackComplete)


        # internal timer for refreshing the plots
        self.plotRefreshTimer = QTimer()
        self.plotRefreshTimer.setInterval(1000)
        self.plotRefreshTimer.timeout.connect(self.signalPlotRefresh)
        self.plotRefreshTimer.start()

        # TODO - what mechanism and what to do when SimulationThread or dies like
        #       refresh GUI and save/close results file??
        # self.simulationThread.finished.connect(self.simulationThreadFinished)
        # self.simulationThread.terminated.connect(self.simulationThreadTerminated)

        # Now that the SimulationThread has been created (but not yet running), connect the
        # Button clicked in MainWindow - call a SimulationThread method to do something
        self.buttonRun.clicked.connect(self.createStartCalculatingSignal)
        self.buttonStop.clicked.connect(self.simulationThread.thread_stop_calculating)
        self.checkboxDistanceBreakpoint.clicked.connect(self.enableBreakpointSpinbox)

        self.simulationThread.start()

    def enableBreakpointSpinbox(self):
        if self.checkboxDistanceBreakpoint.isChecked() is True:
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
        if self.checkboxDistanceBreakpoint.isChecked() is True:
            distance = self.spinboxDistanceBreakpoint.value()
        else:
            # No breakpoint indicated on GUI so run the whole track or
            # until user hits "pause" button
            distance = -1

        # signal the thread
        self.simulationThread.thread_start_calculating(distance)

    def createUserDisplayControls(self):
        self.labelDisplayControl = QLabel("Display Control")

        # Note - FYI - for organizational purposes only -
        # created in the order the controls appear on screen
        self.labelStatus = QLabel("Execution Status")
        self.textboxStatus = QLineEdit("Initialized", self)
        self.textboxStatus.setReadOnly(True)

        self.checkboxDistanceBreakpoint = QCheckBox('Distance Breakpoint (m)', self)
        self.checkboxDistanceBreakpoint.setChecked(False)
        self.spinboxDistanceBreakpoint = QDoubleSpinBox()
        self.spinboxDistanceBreakpoint.setReadOnly(True)
        self.spinboxDistanceBreakpoint.setRange(0, 999999)

        self.buttonRun = QPushButton('Run/Continue', self)
        self.buttonRun.setEnabled(True)
        self.buttonStop = QPushButton('Pause', self)
        self.buttonStop.setEnabled(True)

        # outputs of simulation
        self.labelSimulationIndex = QLabel("Current Sim. Index")
        self.textboxSimulationIndex = QLineEdit("0", self)
        self.textboxSimulationIndex.setReadOnly(False)

        self.labelTime = QLabel("Time (s)")
        self.spinboxTime = QDoubleSpinBox()
        self.spinboxTime.setReadOnly(True)
        self.spinboxTime.setRange(0, 999999)

        self.checkboxDistance = QCheckBox('Distance (m)', self)
        self.checkboxDistance.setChecked(False)
        self.spinboxDistance = QDoubleSpinBox()
        self.spinboxDistance.setReadOnly(True)
        self.spinboxDistance.setRange(0, 999999)

        self.checkboxVelocity = QCheckBox('Velocity (m/s)', self)
        self.checkboxVelocity.setChecked(False)
        self.spinboxVelocity = QDoubleSpinBox()
        self.spinboxVelocity.setReadOnly(True)
        self.spinboxVelocity.setRange(0, 999999)

        self.checkboxAcceleration = QCheckBox('Acceleration (m/s^2)', self)
        self.checkboxAcceleration.setChecked(False)
        self.spinboxAcceleration = QDoubleSpinBox()
        self.spinboxAcceleration.setReadOnly(True)
        self.spinboxAcceleration.setRange(-999999, 999999)

        self.checkboxMotorPower = QCheckBox('Motor Power', self)
        self.checkboxMotorPower.setChecked(False)
        self.spinboxMotorPower = QDoubleSpinBox()
        self.spinboxMotorPower.setReadOnly(True)
        self.spinboxMotorPower.setRange(-999999, 999999)

        self.checkboxBatteryPower = QCheckBox('Battery Power', self)
        self.checkboxBatteryPower.setChecked(False)
        self.spinboxBatteryPower = QDoubleSpinBox()
        self.spinboxBatteryPower.setReadOnly(True)
        self.spinboxBatteryPower.setRange(-999999, 999999)

        self.checkboxBatteryEnergy = QCheckBox('Battery Energy (j)', self)
        self.checkboxBatteryEnergy.setChecked(False)
        self.spinboxBatteryEnergy = QDoubleSpinBox()
        self.spinboxBatteryEnergy.setReadOnly(True)
        self.spinboxBatteryEnergy.setRange(-999999, 999999)

        # self.userDisplayControlsGroup = QtGui.QGroupBox('User Display Controls')
        self.userDisplayControlsGroup = QGroupBox('User Controls')
        # self.userDisplayControlsLayout= QtGui.QGridLayout()
        self.userDisplayControlsLayout = QGridLayout()
        self.userDisplayControlsLayout.addWidget(self.labelStatus,                  0, 0)
        self.userDisplayControlsLayout.addWidget(self.textboxStatus,                0, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxDistanceBreakpoint,   1, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxDistanceBreakpoint,    1, 1)
        self.userDisplayControlsLayout.addWidget(self.buttonRun,                    2, 0)
        self.userDisplayControlsLayout.addWidget(self.buttonStop,                   2, 1)
        self.userDisplayControlsLayout.addWidget(self.labelSimulationIndex,         3, 0)
        self.userDisplayControlsLayout.addWidget(self.textboxSimulationIndex,       3, 1)
        self.userDisplayControlsLayout.addWidget(self.labelTime,                    4, 0)
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
        # TODO placeholder for real work to be done when the SimulationThread
        # SIGNALs MainWindow new data is available in shared memory
        # print('Window SIGNAL from SimulationThread: Results_data_ready')
        time.sleep(0.1)

    def simulationThreadFinished(self):
        # TODO placeholder for SimulationThread SIGNALs ??exiting
        # data is available in shared memory
        # print('Window: SIGNAL From SimulationThread: Finished')
        time.sleep(0.1)

    def simulationThreadTerminated(self):
        # TODO placeholder for SimulationThread SIGNALs terminated
        # print('Window: SIGNAL From SimulationThread: Terminated')
        time.sleep(0.1)

    """
    Slots routines to handle SIGNALs sent to MainWindow from other threads
    (or ourself - e.g. timer expiry)
    """
    @pyqtSlot(str)
    def signalRcvFromSimulationThread(self, text):
        self.textboxStatus.setText(text)

    
    # @pyqtSlot(int)
    # def signalWalkBackComplete(self, walk_back_index):
        """ This function is the handler for the signal sent from SimThread that
        the walk back is complete. We use it to refresh the graphs from the
        passed parameter (walk_back_index) up to sim_index by 
        1) truncating our local copy of the plotted data arrays at dataXXX[0,walk_index] then
        2) rewinding the plotting pointer (self.last_plotted_data=walk_back_index) then
        let the normal refresh mechanism (signalPlotRefresh) append the data
        from walk_back_index to current_sim_index

        Args:
            walk_back_index is the index in data_store arrays where plotted data should be 
            now be refreshed starting at this value through the latest calculation
            (current_sim_index) 
        Returns: 
            Nothing
        """
        #self._velocity = self._velocity[0:walk_back_index]
        # self.last_plotted_index = walk_back_index
        # print("walk_back_index = {}".format(walk_back_index))

    @pyqtSlot()
    def signalPlotRefresh(self):
        # Update the GUI window to display computation status, data, and plots selected by the user
        # This is called periodically because of the signal emitted from plotRefreshTimer
        current_sim_index = (self.data_store.get_simulation_index())
        self.logger.info("MainWindow:", extra={'sim_index': current_sim_index})
        self.textboxSimulationIndex.setText("{}".format(current_sim_index))

        """
        Only refresh data if the simulations calculations have begun, indicated by
        current_sim-index > 0
        Note: current_sim_index is decremented "-1" for the following calls
        because the lap_velocity_simulation calculations may be incomplete for the index
        when this "plot" signal was received and interrupted it. That is, the
        SimulationThread is/could be still updating a DataStore data (lists) records
        simulation_index and not all lists # have been calculated, so we should
        just plot upto the last complete record.
        """
        if current_sim_index > 0:
            """ Refresh our private data to plot from the new (and updated/rewritten) data since
            the last time we were here.
            """

            # Get a dictionary from DataStore containing the lists of updated values
            dictResults = self.data_store.get_new_data_values()
            new_rfi = dictResults['refresh_index']
            updated_time = dictResults['time']
            updated_distance = dictResults['distance']
            updated_velocity = dictResults['velocity']
            updated_max_velocity = dictResults['max_velocity']
            updated_acceleration = dictResults['acceleration']
            updated_motor_power = dictResults['motor_power']
            updated_battery_power = dictResults['battery_power']
            # updated_battery_energy = dictResults['battery_energy']
            # print('len(_x)={} len(_velocity)={}'.format(len(self._x), len(self._velocity)))
            # print('Adding new {} velocity data points starting at index {}'.format(
            #                                                    len(updated_velocity), new_rfi))

            # remove any old data that was recalculated during walk back before appending
            # that refreshed data and any new, additional data
            self._time = self._time[0:new_rfi]
            self._distance = self._distance[0:new_rfi]
            self._velocity = self._velocity[0:new_rfi]
            self._max_velocity = self._max_velocity[0:new_rfi]
            self._acceleration = self._acceleration[0:new_rfi]
            self._motor_power = self._motor_power[0:new_rfi]
            self._battery_power = self._battery_power[0:new_rfi]
            # self._battery_energy = self._battery_energy[0:new_rfi]
            # print('After resizing _velocity is len={}'.format(len(self._velocity)))

            # append on newly retrieved data
            self._time = self._time + updated_time
            self._distance = self._distance + updated_distance
            self._velocity = self._velocity + updated_velocity
            self._max_velocity = self._max_velocity + updated_max_velocity
            self._acceleration = self._acceleration + updated_acceleration
            self._motor_power = self._motor_power + updated_motor_power
            self._battery_power = self._battery_power + updated_battery_power
            # self._battery_energy = self._battery_energy + updated_battery_energy
            self._X = list(range(0, len(self._velocity)))
            # print('After appending, len(_X) = {} len(_velocity) = {}'
            #        .format(len(self._X), len(self._velocity)))

            # update GUI with the last (current) data
            self.spinboxTime.setValue(self._time[-1])
            self.spinboxDistance.setValue(self._distance[-1])
            self.spinboxVelocity.setValue(self._velocity[-1])
            self.spinboxAcceleration.setValue(self._acceleration[-1])
            self.spinboxMotorPower.setValue(self._motor_power[-1])
            self.spinboxBatteryPower.setValue(self._battery_power[-1])
            # self.spinboxBatteryEnergy.setValue(self._battery_energy[-1])

            # alway plot/show the Time plot because the other plots are "linked" to it
            # so user can scroll around
            self.time_data_line.setData(self._X, self._time)

            # selectively display the plots based on the checkboxes
            if self.checkboxDistance.isChecked() is True:
                self.p2.show()
                self.distance_data_line.setData(self._X, self._distance)
            else:
                self.p2.hide()

            if self.checkboxVelocity.isChecked() is True:
                self.p3.show()
                self.max_velocity_data_line.setData(self._X, self._max_velocity)
                self.velocity_data_line.setData(self._X, self._velocity)

            else:
                self.p3.hide()

            if self.checkboxAcceleration.isChecked() is True:
                self.p4.show()
                self.acceleration_data_line.setData(self._X, self._acceleration)
            else:
                self.p4.hide()

            if self.checkboxMotorPower.isChecked() is True:
                self.p5.show()
                self.motor_power_data_line.setData(self._X, self._motor_power)
            else:
                self.p5.hide()

            if self.checkboxBatteryPower.isChecked() is True:
                self.p6.show()
                self.battery_power_data_line.setData(self._X, self._battery_power)
            else:
                self.p6.hide()

            """TBD - to be added once Battery Energy is working in physics_equations
            if self.checkboxBatteryEnergy.isChecked() is True:
                #self.p7.show()
                #self.p7.plot(x=x, y=_battery_energy, name="Plot7", title="Battery Energy (joules)")
                self.battery_energy_data_line.setData(self._X, self._battery_energy)
            else:
                self.p7.hide()
            """
