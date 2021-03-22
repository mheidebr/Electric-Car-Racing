# This application reads eLemons simulations results from a .csv file(s) and displays it

# USE ONLY SI UNITS
import sys
import pandas as pd
# from project_argparser import *
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton)
from PyQt5.QtWidgets import (QApplication, QGridLayout, QGroupBox, QDoubleSpinBox)
import pyqtgraph as pg
import cProfile
import tkinter as tk
from tkinter import filedialog as fd
import os


class ResultsWindow(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, parent=None)

        # Create GUI related resources
        self.setWindowTitle('Race Results')

        # All this TK-related code is to allow the the askopenfile dialogs
        # Also using TK - create an root "window" for the tk askopenfile call
        self.root = tk.Tk()
        # if an askopenfile dialog gets opened, when user is done with it, hide the dialog
        self.root.withdraw()

        # create the user play controls and data results graphs to run the simulation
        self.createUserDisplayControls()

        # create placeholders for the plots MainWindow will delivering (updating)
        # data items into once the data file(s) are opened
        self.graphs = pg.GraphicsLayoutWidget(show=True, title="Race Sim plots")
        self.graphs.resize(1000, 540)
        self.p1 = self.graphs.addPlot(name="Plot1", row=1, col=2,
                                      labels={'bottom': 'time (sec)',
                                              'left': 'Distance (m)'})
        self.p1.addLegend()
        # self.p1.hide()
        self.p2 = self.graphs.addPlot(name="Plot2", row=2, col=2,
                                      labels={'bottom': 'time (sec)',
                                              'left': 'Velocity (m/s)'})
        self.p2.hide()
        self.p3 = self.graphs.addPlot(name="Plot3", row=3, col=2,
                                      labels={'bottom': 'time (sec)',
                                              'left': 'Acceleration (m/s^2)'})
        self.p3.hide()
        self.p4 = self.graphs.addPlot(name="Plot4", row=4, col=2,
                                      labels={'bottom': 'time (sec)',
                                              'left': 'Motor Power (kW)'})
        self.p4.hide()
        self.p5 = self.graphs.addPlot(name="Plot5", row=5, col=2,
                                      labels={'bottom': 'time (sec)',
                                              'left': 'Battery Power (kW)'})
        self.p5.hide()
        self.p6 = self.graphs.addPlot(name="Plot6", row=6, col=2,
                                      labels={'bottom': 'time (sec)',
                                              'left': 'Battery Energy(j)'})
        self.p6.hide()

        # Links user X-coordinate movements of all plots together. Practically, there has
        # to be one plot they all link to, and in this case it's self.p1 (Time)
        self.p2.setXLink(self.p1)
        self.p3.setXLink(self.p1)
        self.p4.setXLink(self.p1)
        self.p5.setXLink(self.p1)
        self.p6.setXLink(self.p1)

        # Layout the major GUI components
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.userDisplayControlsGroup)
        self.layout.addWidget(self.graphs)
        self.setLayout(self.layout)
        
        self._time = [0]

        self.checkboxShowPlotData1.clicked.connect(lambda: self.enablePlotData(1))
        self.checkboxShowPlotData2.clicked.connect(lambda: self.enablePlotData(2))
        self.checkboxDistance.clicked.connect(self.showDistance)
        self.checkboxVelocity.clicked.connect(self.showVelocity)
        self.checkboxAcceleration.clicked.connect(self.showAcceleration)
        self.checkboxMotorPower.clicked.connect(self.showMotorPower)
        self.checkboxBatteryPower.clicked.connect(self.showBatteryPower)
        self.checkboxBatteryEnergy.clicked.connect(self.showBatteryEnergy)
        self.buttonFileOpenPlot1.clicked.connect(lambda: (self.openPlotDataFile(1)))
        self.buttonFileOpenPlot2.clicked.connect(lambda: (self.openPlotDataFile(2)))

    def createUserDisplayControls(self):
        self.labelDisplayControl = QLabel("Display Control")

        # Note - FYI - for organizational purposes only -
        # created in the order the controls appear on screen
        self.checkboxShowPlotData1 = QCheckBox('Show Plot 1', self)
        self.checkboxShowPlotData1.setChecked(False)
        self.checkboxShowPlotData1.setEnabled(False)
        self.buttonFileOpenPlot1 = QPushButton('Select Data File', self)
        self.buttonFileOpenPlot1.setEnabled(True)
        self.textboxPlotDataFilename1 = QLineEdit("", self)
        self.textboxPlotDataFilename1.setReadOnly(False)

        self.checkboxShowPlotData2 = QCheckBox('Show Plot 2', self)
        self.checkboxShowPlotData2.setChecked(False)
        self.checkboxShowPlotData2.setEnabled(False)
        self.buttonFileOpenPlot2 = QPushButton('Select Data File', self)
        self.buttonFileOpenPlot2.setEnabled(True)
        self.textboxPlotDataFilename2 = QLineEdit("", self)
        self.textboxPlotDataFilename2.setReadOnly(False)

        # GUI-related data widgets outputs of simulation
        self.labelSimulationIndex = QLabel("Sim. Index")
        self.textboxSimulationIndex = QLineEdit("0", self)
        self.textboxSimulationIndex.setReadOnly(False)

        self.labelTime = QLabel("Time (s)")
        self.spinboxTime = QDoubleSpinBox()
        self.spinboxTime.setReadOnly(True)
        self.spinboxTime.setRange(0, 999999)

        self.checkboxDistance = QCheckBox('Distance', self)
        self.checkboxDistance.setChecked(True)
        self.checkboxDistance.setEnabled(False)
        self.spinboxDistance = QDoubleSpinBox()
        self.spinboxDistance.setReadOnly(True)
        self.spinboxDistance.setRange(0, 999999)
        self.spinboxDistance2 = QDoubleSpinBox()
        self.spinboxDistance2.setReadOnly(True)
        self.spinboxDistance2.setRange(0, 999999)

        self.checkboxVelocity = QCheckBox('Velocity', self)
        self.checkboxVelocity.setChecked(False)
        self.checkboxVelocity.setEnabled(False)
        self.spinboxVelocity = QDoubleSpinBox()
        self.spinboxVelocity.setReadOnly(True)
        self.spinboxVelocity.setRange(0, 999999)
        self.spinboxVelocity2 = QDoubleSpinBox()
        self.spinboxVelocity2.setReadOnly(True)
        self.spinboxVelocity2.setRange(0, 999999)

        self.checkboxAcceleration = QCheckBox('Acceleration', self)
        self.checkboxAcceleration.setChecked(False)
        self.checkboxAcceleration.setEnabled(False)
        self.spinboxAcceleration = QDoubleSpinBox()
        self.spinboxAcceleration.setReadOnly(True)
        self.spinboxAcceleration.setRange(-999999, 999999)
        self.spinboxAcceleration2 = QDoubleSpinBox()
        self.spinboxAcceleration2.setReadOnly(True)
        self.spinboxAcceleration2.setRange(-999999, 999999)

        self.checkboxMotorPower = QCheckBox('Motor Power', self)
        self.checkboxMotorPower.setChecked(False)
        self.checkboxMotorPower.setEnabled(False)
        self.spinboxMotorPower = QDoubleSpinBox()
        self.spinboxMotorPower.setReadOnly(True)
        self.spinboxMotorPower.setRange(-999999, 999999)
        self.spinboxMotorPower2 = QDoubleSpinBox()
        self.spinboxMotorPower2.setReadOnly(True)
        self.spinboxMotorPower2.setRange(-999999, 999999)

        self.checkboxBatteryPower = QCheckBox('Battery Power', self)
        self.checkboxBatteryPower.setChecked(False)
        self.checkboxBatteryPower.setEnabled(False)
        self.spinboxBatteryPower = QDoubleSpinBox()
        self.spinboxBatteryPower.setReadOnly(True)
        self.spinboxBatteryPower.setRange(-999999, 999999)
        self.spinboxBatteryPower2 = QDoubleSpinBox()
        self.spinboxBatteryPower2.setReadOnly(True)
        self.spinboxBatteryPower2.setRange(-999999, 999999)

        self.checkboxBatteryEnergy = QCheckBox('Battery Energy', self)
        self.checkboxBatteryEnergy.setChecked(False)
        self.checkboxBatteryEnergy.setEnabled(False)
        self.spinboxBatteryEnergy = QDoubleSpinBox()
        self.spinboxBatteryEnergy.setReadOnly(True)
        self.spinboxBatteryEnergy.setRange(-999999, 999999999)
        self.spinboxBatteryEnergy2 = QDoubleSpinBox()
        self.spinboxBatteryEnergy2.setReadOnly(True)
        self.spinboxBatteryEnergy2.setRange(-999999, 999999999)

        # self.userDisplayControlsGroup = QtGui.QGroupBox('User Display Controls')
        self.userDisplayControlsGroup = QGroupBox('User Controls')
        # self.userDisplayControlsLayout= QtGui.QGridLayout()
        self.userDisplayControlsLayout = QGridLayout()
        self.userDisplayControlsLayout.addWidget(self.checkboxShowPlotData1,        1, 1)
        self.userDisplayControlsLayout.addWidget(self.buttonFileOpenPlot1,          2, 1)
        self.userDisplayControlsLayout.addWidget(self.textboxPlotDataFilename1,     3, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxShowPlotData2,        1, 2)
        self.userDisplayControlsLayout.addWidget(self.buttonFileOpenPlot2,          2, 2)
        self.userDisplayControlsLayout.addWidget(self.textboxPlotDataFilename2,     3, 2)
        self.userDisplayControlsLayout.addWidget(self.labelSimulationIndex,         4, 0)
        self.userDisplayControlsLayout.addWidget(self.textboxSimulationIndex,       4, 1)
        self.userDisplayControlsLayout.addWidget(self.labelTime,                    5, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxTime,                  5, 1)
        self.userDisplayControlsLayout.addWidget(self.checkboxDistance,             6, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxDistance,              6, 1)
        self.userDisplayControlsLayout.addWidget(self.spinboxDistance2,             6, 2)
        self.userDisplayControlsLayout.addWidget(self.checkboxVelocity,             7, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxVelocity,              7, 1)
        self.userDisplayControlsLayout.addWidget(self.spinboxVelocity2,             7, 2)
        self.userDisplayControlsLayout.addWidget(self.checkboxAcceleration,         8, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxAcceleration,          8, 1)
        self.userDisplayControlsLayout.addWidget(self.spinboxAcceleration2,         8, 2)
        self.userDisplayControlsLayout.addWidget(self.checkboxMotorPower,           9, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxMotorPower,            9, 1)
        self.userDisplayControlsLayout.addWidget(self.spinboxMotorPower2,           9, 2)
        self.userDisplayControlsLayout.addWidget(self.checkboxBatteryPower,         10, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxBatteryPower,          10, 1)
        self.userDisplayControlsLayout.addWidget(self.spinboxBatteryPower2,         10, 2)
        self.userDisplayControlsLayout.addWidget(self.checkboxBatteryEnergy,        11, 0)
        self.userDisplayControlsLayout.addWidget(self.spinboxBatteryEnergy,         11, 1)
        self.userDisplayControlsLayout.addWidget(self.spinboxBatteryEnergy2,        11, 2)
        self.userDisplayControlsGroup.setFixedWidth(400)
        self.userDisplayControlsGroup.setLayout(self.userDisplayControlsLayout)

    def showDistance(self):
        if self.checkboxDistance.isChecked() is True:
            self.p1.show()
        else:
            self.p1.hide()

    def showVelocity(self):
        if self.checkboxVelocity.isChecked() is True:
            self.p2.show()
        else:
            self.p2.hide()

    def showAcceleration(self):
        if self.checkboxAcceleration.isChecked() is True:
            self.p3.show()
        else:
            self.p3.hide()

    def showMotorPower(self):
        if self.checkboxMotorPower.isChecked() is True:
            self.p4.show()
        else:
            self.p4.hide()

    def showBatteryPower(self):
        if self.checkboxBatteryPower.isChecked() is True:
            self.p5.show()
        else:
            self.p5.hide()

    def showBatteryEnergy(self):
        if self.checkboxBatteryEnergy.isChecked() is True:
            self.p6.show()
        else:
            self.p6.hide()

    def openPlotDataFile(self, plot_number):

        path_and_name = fd.askopenfilename(filetypes=[("Comma Sep Values", ".csv")])
        if not path_and_name:
            print("path_and_name not selected ={}".format(path_and_name))
            # self.root.destroy()
            return

        name, ext = os.path.splitext(os.path.basename(path_and_name))
        print("opening plot number {}, with name {}".format(int(plot_number), name+ext))

        # get rid of tk dialog window

        if plot_number == 1:
            self.textboxPlotDataFilename1.setText(name+ext)
            self.checkboxShowPlotData1.setEnabled(True)
            self.checkboxShowPlotData1.setChecked(True)

            # Read in the new data file for plot #1
            self.data_frame = pd.read_csv(name+ext, delimiter=',')
            
            # use the dictionary property to select out and assign to our private variables
            # the file's data values
            self._sim_index = self.data_frame['SimulationIndex']
            self._time = self.data_frame['Time']
            self._distance = self.data_frame['Distance']
            self._velocity = self.data_frame['Velocity']
            self._max_velocity = self.data_frame['Max Velocity']
            self._acceleration = self.data_frame['Acceleration']
            self._motor_power = self.data_frame['Motor Power']/1000
            self._battery_power = self.data_frame['Battery Power']/1000
            self._battery_energy = self.data_frame['Battery Energy']

            # Create plottable items (the lines) but don't yet display them
            self.distance_data_line = pg.PlotDataItem(self._time, self._distance, name='Plot 1',
                                                      pen='w')
            self.velocity_data_line = pg.PlotDataItem(self._time, self._velocity,
                                                      pen='w')
            self.max_velocity_data_line = pg.PlotDataItem(self._time, self._max_velocity,
                                                          pen='r')
            self.acceleration_data_line = pg.PlotDataItem(self._time, self._acceleration,
                                                          pen='w')
            self.motor_power_data_line = pg.PlotDataItem(self._time, self._motor_power,
                                                         pen='w')
            self.battery_power_data_line = pg.PlotDataItem(self._time, self._battery_power,
                                                           pen='w')
            self.battery_energy_data_line = pg.PlotDataItem(self._time, self._battery_energy,
                                                            pen='w')
            # add the lines to the respective plot widget. 
            # The plot widget (e.g. p1, p2,...) show() methods determines if the graph is showing
            self.p1.addItem(self.distance_data_line)
            self.p2.addItem(self.velocity_data_line)
            self.p2.addItem(self.max_velocity_data_line)
            self.p3.addItem(self.acceleration_data_line)
            self.p4.addItem(self.motor_power_data_line)
            self.p5.addItem(self.battery_power_data_line)
            self.p6.addItem(self.battery_energy_data_line)

        if plot_number == 2:
            self.textboxPlotDataFilename2.setText(name+ext)
            self.checkboxShowPlotData2.setEnabled(True)
            self.checkboxShowPlotData2.setChecked(True)

            # Read in the new data file for plot #2
            self.data_frame2 = pd.read_csv(name+ext, delimiter=',')
            self._sim_index2 = self.data_frame2['SimulationIndex']
            self._time2 = self.data_frame2['Time']
            self._distance2 = self.data_frame2['Distance']
            self._velocity2 = self.data_frame2['Velocity']
            self._max_velocity2 = self.data_frame2['Max Velocity']
            self._acceleration2 = self.data_frame2['Acceleration']
            self._motor_power2 = self.data_frame2['Motor Power']/1000
            self._battery_power2 = self.data_frame2['Battery Power']/1000
            self._battery_energy2 = self.data_frame2['Battery Energy']

            # Create plottable items (the lines) but don't yet display them
            self.distance_data_line2 = pg.PlotDataItem(self._time2, self._distance2, name='Plot 2',
                                                       pen='g')
            self.velocity_data_line2 = pg.PlotDataItem(self._time2, self._velocity2,
                                                       pen='g')
            self.max_velocity_data_line2 = pg.PlotDataItem(self._time2, self._max_velocity2,
                                                           pen='y')
            self.acceleration_data_line2 = pg.PlotDataItem(self._time2, self._acceleration2,
                                                           pen='g')
            self.motor_power_data_line2 = pg.PlotDataItem(self._time2, self._motor_power2,
                                                          pen='g')
            self.battery_power_data_line2 = pg.PlotDataItem(self._time2, self._battery_power2,
                                                            pen='g')
            self.battery_energy_data_line2 = pg.PlotDataItem(self._time2, self._battery_energy2,
                                                             pen='g')
            # add the lines to the respective plot widget.
            # If the plot widget is showing (e.g. show(), the line will appear.
            self.p1.addItem(self.distance_data_line2)
            self.p2.addItem(self.velocity_data_line2)
            self.p2.addItem(self.max_velocity_data_line2)
            self.p3.addItem(self.acceleration_data_line2)
            self.p4.addItem(self.motor_power_data_line2)
            self.p5.addItem(self.battery_power_data_line2)
            self.p6.addItem(self.battery_energy_data_line2)
                                            
        # show the appropriate plots if GUI has them turned on
        self.enablePlotData(plot_number)
    
    def enablePlotData(self, plot_number):
        # Assumption:
        # 1) the data file for the parameter "plot_number" has already been opened and
        # contents stored in the respective lists (e.g. self.distanace_data_line2)
        # 2) it is assumed that checkboxShowPlotX.setChecked has already been called
        if plot_number == 1:
            # see if we're supposed show plot 1 data items. If so load them up
            # Note: the .show() 
            if self.checkboxShowPlotData1.isChecked() is True:
                self.p1.addItem(self.distance_data_line)
                self.p2.addItem(self.velocity_data_line)
                self.p2.addItem(self.max_velocity_data_line)
                self.p3.addItem(self.acceleration_data_line)
                self.p4.addItem(self.motor_power_data_line)
                self.p5.addItem(self.battery_power_data_line)
                self.p6.addItem(self.battery_energy_data_line)
            else:
                # hide (remove) from view all plot 1 data
                self.p1.removeItem(self.distance_data_line)
                self.p2.removeItem(self.velocity_data_line)
                self.p2.removeItem(self.max_velocity_data_line)
                self.p3.removeItem(self.acceleration_data_line)
                self.p4.removeItem(self.motor_power_data_line)
                self.p5.removeItem(self.battery_power_data_line)
                self.p6.removeItem(self.battery_energy_data_line)

        if plot_number == 2:
            if self.checkboxShowPlotData2.isChecked() is True:
                # add our 2nd file's data back to the plots
                self.p1.addItem(self.distance_data_line2)
                self.p2.addItem(self.velocity_data_line2)
                self.p2.addItem(self.max_velocity_data_line2)
                self.p3.addItem(self.acceleration_data_line2)
                self.p4.addItem(self.motor_power_data_line2)
                self.p5.addItem(self.battery_power_data_line2)
                self.p6.addItem(self.battery_energy_data_line2)

            else:
                # remove the 2nd file's data from the plots
                self.p1.removeItem(self.distance_data_line2)
                self.p2.removeItem(self.velocity_data_line2)
                self.p2.removeItem(self.max_velocity_data_line2)
                self.p3.removeItem(self.acceleration_data_line2)
                self.p4.removeItem(self.motor_power_data_line2)
                self.p5.removeItem(self.battery_power_data_line2)
                self.p6.removeItem(self.battery_energy_data_line2)

        if self.checkboxShowPlotData1.isChecked() is False and \
           self.checkboxShowPlotData2.isChecked() is False:
            # Don't show any data or allow checkbox selection of parameters
            self.checkboxDistance.setEnabled(False)
            self.checkboxVelocity.setEnabled(False)
            self.checkboxAcceleration.setEnabled(False)
            self.checkboxMotorPower.setEnabled(False)
            self.checkboxBatteryPower.setEnabled(False)
            self.checkboxBatteryEnergy.setEnabled(False)
        else:
            # if either Show Plot checkbox is selected, allow user to select plots
            self.checkboxDistance.setEnabled(False)
            self.checkboxVelocity.setEnabled(True)
            self.checkboxAcceleration.setEnabled(True)
            self.checkboxMotorPower.setEnabled(True)
            self.checkboxBatteryPower.setEnabled(True)
            self.checkboxBatteryEnergy.setEnabled(True)


if __name__ == "__main__":

    """
    logger = logging.getLogger(__name__)

    args = call_args()
    if args["logging_arg"].arg_check(args["parsed_args"].logging):
        configure_logging()

    car_data = args["car_arg"].open_car_dict(args["parsed_args"].car)
    track_data = args["track_arg"].open_track_dict(args["parsed_args"].track)

    data_store = DataStore()
    logger.info("MainWindow: DataStore initialized",
                    extra={'sim_index': data_store.get_simulation_index()})
    simulation_thread = SimulationThread(data_store, logger)
    """

    MainApp = QApplication(sys.argv)
    window = ResultsWindow()
    window.show()
    sys.exit(cProfile.runctx("MainApp.exec_()", globals(), locals(), 'profile-display.out'))
