# The actual simulation goes here
# USE ONLY SI UNITS
import sys
import time
import logging
import threading
from PyQt5 import QtWidgets
import pyqtgraph as pg


from physics_equations import (max_negative_power_physics_simulation,
                               max_positive_power_physics_simulation,
                               constrained_velocity_physics_simulation,
                               )
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties

from logging_config import configure_logging
from datastore import (DataStore,
                       RacingSimulationResults,
                       )

logger = logging.getLogger(__name__)


def racing_simulation(data_store):
    """Function accepts a car and a track and executes
    a simulation to ouput critical metrics related
    to battery life and track speed.

    Args:
        data_store (DataStore): Thread safe storage for all simulation data

    Returns:
        Nothing (all data saved in the datastore)

    """
    results = RacingSimulationResults()

    lap_results = lap_velocity_simulation(data_store)
    # only calculate results if the simulation ran through without an interruption
    if not data_store.exit_event.is_set():
        car = data_store.get_car_properties()
        results.laps_per_pit_stop = car.battery_capacity / lap_results.battery_energy_profile[-1]
        results.lap_time = lap_results.end_velocity
        results.lap_results = lap_results
        data_store.set_race_results(results)


def lap_velocity_simulation(data_store):
    """Function calculates the velocity profile of a car with
    car_properties on a track with track_properties. The car
    starts with an ititial velocity of initial_velocity.

    Args:
        data_store (DataStore): Thread safe storage for all simulation data

    Returns:
        Nothing (all data saved in the datastore)
    """
    track = data_store.get_track_properties()
    car = data_store.get_car_properties()

    sim_index = data_store.get_simulation_index()
    # need to populate the time profile be the same length as the distance list
    # to complete a lap of simulation
    while sim_index < len(track.distance_list) and not data_store.exit_event.is_set():
        try:
            distance_of_travel = (track.distance_list[sim_index + 1] -
                                  track.distance_list[sim_index])
        except IndexError as e:
            logger.error("index error: {}\n{}".format(track.distance_list[sim_index], e),
                         extra={'sim_index': sim_index})
        velocity = data_store.get_velocity()
        physics_results = max_positive_power_physics_simulation(velocity,
                                                                distance_of_travel,
                                                                car,
                                                                track)
        # check if velocity constraints are violated
        if physics_results.final_velocity > track.max_velocity_list[sim_index]:
            # velocity constraint violated!!
            # start walking back until velocity constraint at sim_index is met
            logger.info("velocity constraint violated starting walk back, current v: {}, max: {}"
                        .format(physics_results.final_velocity, track.max_velocity_list[sim_index]),
                        extra={'sim_index': data_store.get_simulation_index()})
            while data_store.get_velocity_at_index(sim_index) > track.max_velocity_list[sim_index]:
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
                walk_back_counter = data_store.get_walk_back_counter()
                sim_index = data_store.get_simulation_index()
                recalculation_start_index = sim_index - walk_back_counter
                recalculation_end_index = sim_index - 1
                logger.info("starting and ending walkback index: {}, {}"
                            .format(recalculation_start_index, recalculation_end_index),
                            extra={'sim_index': data_store.get_simulation_index()})
                for i in range((sim_index - walk_back_counter), (sim_index - 1)):
                    velocity = data_store.get_velocity_at_index(i - 1)
                    # recalculate with negative motor power
                    results = max_negative_power_physics_simulation(velocity,
                                                                    distance_of_travel,
                                                                    car,
                                                                    track)
                    data_store.add_physics_results_to_lap_results(results, i)

                velocity = data_store.get_velocity_at_index(sim_index - 1)
                # last deceleration will be a constrained velocity because
                # it will be neither max positive or negative motor power
                physics_results = \
                    constrained_velocity_physics_simulation(velocity,
                                                            track.max_velocity_list[sim_index],
                                                            distance_of_travel,
                                                            car,
                                                            track)
                # check if constrained velocity calculation is realistic
                # TODO other checks here can be on acceleration or wheel force
                if abs(physics_results.motor_power) > abs(car.motor_power):
                    logger.info("velocity constraint still violated, calculated power: {}, max power: {}"
                                .format(physics_results.motor_power, car.motor_power),
                                extra={'sim_index': data_store.get_simulation_index()})
                    logger.info("sim_index, walkback: {} {}, incrementing walk back"
                                .format(sim_index, walk_back_counter),
                                extra={'sim_index': data_store.get_simulation_index()})
                    data_store.increment_walk_back_counter()
                else:
                    logger.info("constrained velocity equation accepted",
                                extra={'sim_index': data_store.get_simulation_index})
                    data_store.add_physics_results_to_lap_results(results, sim_index)

            # reset walk back index
            data_store.reset_walk_back_counter()
        velocity = data_store.get_velocity_at_index(sim_index)
        data_store.set_velocity(velocity)
        data_store.increment_simulation_index()


class SimulationThread(threading.Thread):
    """Wrapper class for running the the simulation.
    """
    def __init__(self, data_store, *args, **kwargs):
        super().__init__(daemon=True, *args, **kwargs)
        self._data_store = data_store

    def run(self):
        racing_simulation(self._data_store)


class VisualizationThread(threading.Thread):
    """Wrapper class for running the visualization part of
    the simulation.

    """

    def __init__(self, data_store, *args, **kwargs):
        super().__init__(daemon=True, *args, **kwargs)
        QtWidgets.QApplication(sys.argv)
        self._data_store = data_store
        self._display_window = MainWindow()

    def run(self):
        while not self._data_store.exit_event.is_set():

            current_lap_results = self._data_store.get_lap_results()
            time = current_lap_results.time_profile
            velocity = current_lap_results.velocity_profile
            distance = current_lap_results.distance_profile
            self._display_window.regraph(time, distance, velocity)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.graphWidget.show()

    def regraph(self, time_list, distance, velocity):
        # plot data: x, y values
        self.graphWidget.plot(time, distance)
        self.graphWidget.plot(time, velocity)


# rotational inertia estimation: http://www.hpwizard.com/rotational-inertia.html
def main():
    data_store = DataStore()

    configure_logging()

    data_store = DataStore()

    segment_distance = 0.01  # 1cm
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

    track.add_critical_point(0, 10, track.FREE_ACCELERATION)
    track.add_critical_point(10, 5, track.FREE_ACCELERATION)
    track.add_critical_point(2000, 100, track.FREE_ACCELERATION)
    track.generate_track_list(segment_distance)

    car = ElectricCarProperties()
    car.set_car_parameters(mass=mass, rotational_inertia=rotational_inertia,
                           motor_power=battery_power, motor_efficiency=motor_efficiency,
                           battery_capacity=10, drag_coefficient=drag_coefficient,
                           frontal_area=frontal_area, wheel_radius=wheel_radius)

    data_store.initialize_lap_profiles(len(track.distance_list))
    data_store.set_car_properties(car)
    data_store.set_track_properties(track)

    # create threads
    simulation_thread = SimulationThread(data_store)
    #visualization_thread = VisualizationThread(data_store)
    print("threads set up")
    time.sleep(3)
    simulation_thread.start()
    #visualization_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt... Shutting down", extra={'sim_index': 'N/A'})
    finally:
        data_store.exit_event.set()

        simulation_thread.join()
        #visualization_thread.join()


if __name__ == '__main__':
    main()
