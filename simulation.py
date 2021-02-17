# The actual simulation code goes here
#
# To Execute see visualization.py
#

# USE ONLY SI UNITS
import time
import logging
# from project_argparser import SingleArg
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot)
import cProfile
#import ptvsd
from datastore import (DataStore, RacingSimulationResults)
from logging_config import configure_logging
from physics_equations import (max_negative_power_physics_simulation,
                               max_positive_power_physics_simulation,
                               constrained_velocity_physics_simulation,
                               reverse_max_negative_power_physics_simulation
                               )
from electric_car_properties import ElectricCarProperties
from track_properties import (TrackProperties,
                              high_plains_raceway)
# from track_properties import (TrackProperties,
#                              simple_track)


class SimulationThread(QThread):
    # Define the Signals we'll be emitting to the MainWindow
    simulationThreadSignal = pyqtSignal(str)
    simulationThreadWalkBackCompleteSignal = pyqtSignal(int)  # sim_index where walkback completed
    breakpointDistance = 0

    def __init__(self, passed_data_store, logger, track_data, car_data, parent=None):
        QThread.__init__(self, parent)
        
        self.logger = logger

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
        self.initialize_race(track_data, car_data)

        # print('SimulationThread: __init()__')
        # print("SimulationThread: Simulation Index = {}".format(self._data_store.\
        # get_simulation_index()))

        # connect some signals from the main window to us
        # self.connect(self, QtCore.SIGNAL('To_End',self.processToEnd)

    def __del__(self):
        # Before a SimulationThread object is destroyed, we need to ensure that it stops processing.
        # For this reason, we implement the following method in a way that indicates to
        # the part of the object that performs the processing that it must stop, and waits
        # until it does so.
        self.exiting = True
        self.wait()

        # rotational inertia estimation: http://www.hpwizard.com/rotational-inertia.html

    def initialize_race(self, track_data, car_data):

        segment_distance = 0.005  # meters, this must be very very small
        wheel_radius = 0.25  # m, ~20 in OD on tires

        track = TrackProperties()
        track.set_air_density(track_data["air_density"])


        for distance in high_plains_raceway:
            if str(distance) not in "air_density":
                track.add_critical_point(distance, track_data[distance],
                                        track.FREE_ACCELERATION)
        # for distance in simple_track:
        #    track.add_critical_point(distance, simple_track[distance], track.FREE_ACCELERATION)
        track.generate_track_list(segment_distance)

        car = ElectricCarProperties()
        car.set_car_parameters(mass=car_data["vehKg"], rotational_inertia=car_data["wheelInertiaKgM2"],
                               motor_power=(car_data["maxMotorKw"] * 1000), motor_efficiency=car_data["motorPeakEff"],
                               battery_capacity=10, drag_coefficient=car_data["dragCoef"],
                               frontal_area=car_data["frontalAreaM2"], wheel_radius=wheel_radius,
                               wheel_pressure_bar=car_data["wheelRrCoef"])

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
        # print("Breakpoint Distance value:{}".format(distance_value))
        self.logger.info('Slot:thread_start_calculating :',
                    extra={'sim_index': self._data_store.get_simulation_index()})

        if distance_value == 0:
            self.logger.info('Slot:thread_start_calculating SINGLE STEP NOT IMPLEMENTED:',
                        extra={'sim_index': self._data_store.get_simulation_index()})

            # TODO - finish this breakpoint case
            self.simulationComputing = False

        elif distance_value == -1:
            self.logger.info('Slot:thread_start_calculating RUN TO COMPLETION :',
                        extra={'sim_index': self._data_store.get_simulation_index()})
            # set the breakpoint to be a very large number to indicate run to completion
            self.breakpointDistance = 9999999
            # (re)start computing and acknowledge to MainWindow by sending a signal back
            self.simulationThreadSignal.emit("Calculating...")
            # "state" variable indicating thread should be calculating
            self.simulationComputing = True
        else:
            # run to the distance value point in the track
            sim_index = self._data_store.get_simulation_index()
            if distance_value > self._data_store.get_distance_at_index(sim_index):
                self.logger.info('Slot:thread_start_calculating RUN TO DISTANCE :',
                            extra={'sim_index': sim_index})
                # requested breakpoint is further down the track
                self.breakpointDistance = distance_value
                # Start computing and acknowledge to MainWindow by sending a signal back
                self.simulationThreadSignal.emit("Calculating...")
                # "state" variable indicating thread should be calculating
                self.simulationComputing = True
            else:
                self.logger.info('Slot:thread_start_calculating PAST REQUESTED DISTANCE :',
                            extra={'sim_index': sim_index})
                # simulation has already past this point in the track, don't proceed
                self.simulationComputing = False

    @pyqtSlot()
    def thread_stop_calculating(self):
        self.logger.info('Slot:thread_stop_calculating :',
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
            # results.laps_per_pit_stop = car["battery_capacity"]/lap_results.motor_energy_list[-1]
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
        get_final_velocity = self._data_store.get_final_velocity_at_index

        track = self._data_store.get_track_properties()
        air_density = track.get_air_density()
        car = self._data_store.get_car_properties()

        # need to populate the time profile be the same length as the distance list
        # to complete a lap of simulation
        list_len = len(track.distance_list)
        self.logger.debug('track.distance_list length={}'.format(list_len),
                     extra={'sim_index': self._data_store.get_simulation_index()})

        # TODO - Add self.simulationComputing to loop control to while
        while self._data_store.get_simulation_index() < (list_len - 1):

            # get the new index we are going to calculate
            sim_index = self._data_store.get_simulation_index()

            if self._data_store.exit_event.is_set():
                break
            distance_of_travel = (track.distance_list[sim_index + 1] -
                                  track.distance_list[sim_index])

            # only continue simulation computing if the GUI says to do so.
            if (self.simulationComputing is True and self.breakpointDistance > track.distance_list[sim_index]): 
                initial_velocity = get_final_velocity(sim_index - 1)
                physics_results = max_positive_power_physics_simulation(initial_velocity,
                                                                        distance_of_travel,
                                                                        car,
                                                                        air_density)
                add_physics_result_to_datastore(physics_results, sim_index)
                # check if velocity constraints are violated
                if get_final_velocity(sim_index) > track.max_velocity_list[sim_index]:
                    # velocity constraint violated!!
                    # start walking back until velocity constraint at sim_index is met
                    self.logger.debug("velocity constraint violated starting walk back, current v: {}, max: {}"
                        .format(physics_results.final_velocity, track.max_velocity_list[sim_index]),
                        extra={'sim_index': self._data_store.get_simulation_index()})
                    self.walk_back(track.max_velocity_list[sim_index], track, car)

                # completed calculation for the latest simulation index,
                self._data_store.increment_simulation_index()
            else:
                # self.simulationComputing is False or we've reached a breakpoint,
                # so wait for GUI user to indicate proceed

                if self.simulationComputing is True:
                    # if we're computing and got here, must have hit a breakpoint, therefore pause
                    # Now send a signal back to the main window
                    self.simulationThreadSignal.emit("Paused")

                    # "state" variable indicating thread should stop calculating
                    self.simulationComputing = False

                # else:
                    # we've began not computing or a breakpoint already has sent us there
                    # so do nothing more than waitk

                # in any case, wait until user gives us a new condition to continue computing
                time.sleep(1.0)
                self.logger.debug("waiting for simulationComputing==True",
                             extra={'sim_index': sim_index})
        # end of while data_store.get_simulation_index() < list_len:

        self.logger.info("SIMULATION COMPLETE!", extra={'sim_index': 'N/A'})
        self.simulationThreadSignal.emit("Finished!")
        self._data_store.exit_event.set()

    def walk_back(self, velocity_from_constraint, passed_track, passed_car):
        """This functions purpose is to correct some of the track calculations after
        a velocity constraint is violated. The calculations start at the index
        where the violation was found and then goes backwards along the track to 
        create a braking profile until the braking profile meets up with the previous
        acceleration profile.

        Args:
            velocity_from_constraint (float): maximum velocity allowed. This should be
                the max velocity constraint value.
            track (TrackProperties): reference to track properties of simulatoin
            car (CarProperties): reference to car properties of simulation
        
        Returns:
            Nothing, all results saved to datastore


        """
        #ptvsd.debug_this_thread()
        # performance increases by assigning local functions
        # https://towardsdatascience.com/10-techniques-to-speed-up-python-runtime-95e213e925dc
        add_physics_result_to_datastore = self._data_store.add_physics_results_to_lap_results
        get_initial_velocity = self._data_store.get_initial_velocity_at_index
        get_final_velocity = self._data_store.get_final_velocity_at_index

        track = passed_track
        air_density = track.get_air_density()
        car = passed_car
        sim_index = self._data_store.get_simulation_index()

        walk_back_status = "walk back started"

        while(walk_back_status == "walking back" or walk_back_status == "walk back started"):
            """This while loop's purpose is to recalculate a portion of the
            car's car profile because the car ended up going too fast at a point on the
            track. To recalculate the following happens:

            1. a "walk back" index is used to track how far back the recalculation occurs
            2. The simulation is run backward on the track, and back in time
            3. The calculation that occurs is a maximum deceleration calculation
            4. Once the calculation occurs the velocity at (sim_index - walk_back_index) is compared
            to the velocity in the datastore at (sim_index - walk_back_index) and the following happens
                a. if the calculated velocity is lower than the datastore velocity the walk_back_index
                is incremented and the calculation is run again
                b.  if the caluclated velocity is higher than the datastore velocity then the calculation 
                is thrown out and a constrained velocity calculation is made 
                c.  if the velocity is the same then the calculation is accepted
            5. Once b. or c. is executed the walkback is complete and all variables are reset, the 
            walk back calculations are committed to the datastore and the simulation continues

            """
            walk_back_index = sim_index - self._data_store.get_walk_back_counter()
            
            distance_of_travel = (track.distance_list[walk_back_index] -
                                  track.distance_list[walk_back_index - 1])
            
            # the velocity used for the reverse physics calculation
            # use the constraint velocity to start the reverse calculation
            if(walk_back_status == "walk back started"):
                walk_back_status = "walking back"
                current_velocity = velocity_from_constraint
            elif(walk_back_status == "walking back"):
                current_velocity = get_initial_velocity(walk_back_index + 1)
            else: 
                raise("incorrect walk back status set: {}".format(walk_back_status))

            # we need to compare the velocity that is in the datastore from the final velocity at 
            # the previous index
            comparison_velocity = get_final_velocity(walk_back_index - 1)  # comparing against the final v

            self.logger.debug("walk_back_index: {}, end_v: {}, start_v: {}"
                        .format(walk_back_index, current_velocity, comparison_velocity),
                        extra={'sim_index': self._data_store.get_simulation_index()})

            self.logger.debug("velocity: {}"
                         .format(current_velocity),
                         extra={'sim_index': walk_back_index})

            # run reverse max decleration equation
            physics_results = reverse_max_negative_power_physics_simulation(current_velocity,
                                                                            distance_of_travel,
                                                                            car,
                                                                            air_density)
            self.logger.debug("physics.initial_v: {}, current_v: {}, comparison_v: {}, walk_indx: {}, walk_cnt: {}"
                        .format(physics_results.initial_velocity, current_velocity, comparison_velocity, walk_back_index, self._data_store.get_walk_back_counter()),
                        extra={'sim_index': self._data_store.get_simulation_index()})                                                            
            # compare resulting velocity against datastore velocity
            if(physics_results.initial_velocity < comparison_velocity):
                #commit results, increment walkback counter and continue
                add_physics_result_to_datastore(physics_results, walk_back_index)
                self._data_store.increment_walk_back_counter()
            elif(physics_results.initial_velocity == comparison_velocity):
                add_physics_result_to_datastore(physics_results, walk_back_index)
                walk_back_status = "walk back complete"
            elif(physics_results.initial_velocity > comparison_velocity):
                physics_results = \
                    constrained_velocity_physics_simulation(current_velocity,
                                                            comparison_velocity,
                                                            distance_of_travel,
                                                            car,
                                                            air_density)
                add_physics_result_to_datastore(physics_results, walk_back_index)
                walk_back_status = "walk back complete"
                self.logger.debug("walkback complete, constrained physics",
                        extra={'sim_index': self._data_store.get_simulation_index()})
            else:
                raise("Something wrong in walk back! Please contact you local dev for more information")

        # walk back complete, let the main graphing entity know where we ended up
        # refresh_index = self._data_store.get_simulation_index()-walk_back_index
        # self. simulationThreadWalkBackCompleteSignal.emit(walk_back_index)
        self._data_store.set_refresh_index(walk_back_index)
        # reset walk back index for next time
        self._data_store.reset_walk_back_counter()
 

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment with the thread's start() method has been setup,
        # and then runs "continuously"
        self.logger.info("SimulationThread: entering cProfile.runctx() ",
                    extra={'sim_index': 'N/A'})

        # profiling tool, look at results with runsnake:
        # https://kupczynski.info/2015/01/16/profiling-python-scripts.html
        # this has relatively little overhead for the overall runtime of the program
        # I have only been able to get the runsnake files to work on linux
        # alternative profile results viewer for windows (untried):
        # https://sourceforge.net/projects/qcachegrindwin/
        cProfile.runctx("self.racing_simulation()", globals(), locals(), 'profile-simulation.out')
