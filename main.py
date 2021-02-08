#This is the driver code that launches the GUI (MainWindow), which in turn begins the simulation (SimulationThread). 
#Arguments, for options including logging, csv file loading and csv file output are taken care of here, as well. 
#
#To launch: python3 main.py -l [on|off] -c [car csv file name -- defaults to included file] -t [track csv file name -- defaults to included file] -o [desired output file name]
#

import sys
import time
import logging
import cProfile
from project_argparser import (SingleArg, call_args)
from visualization import MainWindow
from logging_config import configure_logging
from PyQt5.QtWidgets import (QApplication, QGridLayout, QGroupBox, QDoubleSpinBox)

if __name__ == "__main__":
    
    args = call_args()

    if args["logging_arg"].arg_check(args["parsed_args"].logging):
        configure_logging()
    
    car_data = args["car_arg"].open_car_dict(args["parsed_args"].car)
    track_data = args["track_arg"].open_track_dict(args["parsed_args"].track)

    MainApp = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(cProfile.runctx("MainApp.exec_()", globals(), locals(), 'profile-display.out'))
