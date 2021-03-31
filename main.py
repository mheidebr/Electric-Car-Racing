#This is the driver code that launches the GUI (MainWindow), which in turn begins the simulation (SimulationThread). 
#Arguments, for options including logging, csv file loading and csv file output are taken care of here, as well. 
#
#To launch: python3 main.py -l [on|off] -c [car csv file name -- defaults to included file] -t [track csv file name -- defaults to included file] -o [desired output file name]
#

import sys
import time
import logging
import cProfile
from project_argparser import (SingleArg, call_args, call_ini)
from visualization import MainWindow
from simulation import SimulationThread
from datastore import DataStore
from logging_config import configure_logging
from PyQt5.QtWidgets import (QApplication, QGridLayout, QGroupBox, QDoubleSpinBox)

if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    args = call_args()
    init_vals = call_ini()
    if args["logging_arg"].arg_check(args["parsed_args"].logging):
        configure_logging()

    output_filename = args["parsed_args"].output

    car_data = args["car_arg"].open_car_dict(args["parsed_args"].car)
    track_data = args["track_arg"].open_track_dict(args["parsed_args"].track)

    data_store = DataStore()
    logger.info("MainWindow: DataStore initialized",
                    extra={'sim_index': data_store.get_simulation_index()})
    simulation_thread = SimulationThread(data_store, logger, track_data, car_data, init_vals)

    MainApp = QApplication(sys.argv)
    window = MainWindow(data_store, simulation_thread, logger, output_filename)
    window.show()

    sys.exit(cProfile.runctx("MainApp.exec_()", globals(), locals(), './results/cProfile-results/profile-display.out'))
