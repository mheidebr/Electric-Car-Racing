# The actual simulation goes here
# USE ONLY SI UNITS
import sys
import os
import time
import logging
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from copy import deepcopy, copy
import threading


from physics_equations import (max_negative_power_physics_simulation,
                               max_positive_power_physics_simulation,
                               constrained_velocity_physics_simulation,
                               )
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties

from logging_config import configure_logging
from datastore import (DataStore,
                       RacingSimulationResults,
                       LapVelocitySimulationResults,
                       )

logger = logging.getLogger(__name__)


def racing_simulation(data_store,
                      car: ElectricCarProperties,
                      track: TrackProperties,
                      main_window):
    """Function accepts a car and a track and executes
    a simulation to ouput critical metrics related
    to battery life and track speed.

    Args:
        car (ElectricCarProperties): Characteristics of car being simulated
        track (TrackProperties): Characteristics of track being simulated

    Returns:
        results (RacingSimulationResults): output of the simulation

    """
    results = RacingSimulationResults()

    lap_results = lap_velocity_simulation(data_store, car, track, main_window)
    results.laps_per_pit_stop = car.battery_capacity / lap_results.battery_energy_profile[-1]
    results.lap_time = lap_results.end_velocity
    results.lap_results = lap_results

    return results


def lap_velocity_simulation(data_store,
                            car: ElectricCarProperties,
                            track: TrackProperties,
                            main_window):
    """Function calculates the velocity profile of a car with
    car_properties on a track with track_properties. The car
    starts with an ititial velocity of initial_velocity.

    Args:
        initial_velocity (double): initial velocity of the car at time = 0
        delta_distance (double): length over which each physics simulation is done
        car (ElectricCarProperties): Characteristics of car being simulated
        track (TrackProperties): Characteristics of track being simulated

    Returns:
        results (LapVelocitySimulationResults): output of the lap simulation
    """

    lap_results = LapVelocitySimulationResults(len(track.max_velocity_list), main_window)

    sim_index = data_store.get_simulation_index()
    # need to populate the time profile be the same length as the distance list
    # to complete a lap of simulation
    while sim_index < len(track.distance_list):
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
            while lap_results.velocity_profile[sim_index] > track.max_velocity_list[sim_index]:
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
                    velocity = lap_results.velocity_profile[i - 1]
                    # recalculate with negative motor power
                    results = max_negative_power_physics_simulation(velocity,
                                                                    distance_of_travel,
                                                                    car,
                                                                    track)
                    lap_results.add_physics_results(results, i)

                velocity = lap_results.velocity_profile[sim_index - 1]
                # last deceleration will be a constrained velocity because
                # it will be neither max positive or negative motor power
                physics_results = constrained_velocity_physics_simulation(velocity,
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
                                extra={'sim_index': data_store.get_simulation_index()})
                    lap_results.add_physics_results(results, sim_index)

            # reset walk back index
            data_store.reset_walk_back_counter()

        data_store.set_velocity(lap_results.velocity_profile[sim_index])
        data_store.increment_simulation_index()

    return lap_results


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

    def regraph(self, time, distance, velocity):
        # plot data: x, y values
        self.graphWidget.plot(time, distance)
        self.graphWidget.plot(time, velocity)


# rotational inertia estimation: http://www.hpwizard.com/rotational-inertia.html
def main():

    data_store = DataStore()

    configure_logging(data_store)

    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    segment_distance = 0.01  # 1cm
    battery_power = 40000  # 40kW
    motor_efficiency = 0.8
    wheel_radius = 0.25  # m, ~20 in OD on tires
    rotational_inertia = 10  # kg*m^2
    mass = 1000  # kg
    drag_coefficient = 0.4
    frontal_area = 7  # m^2
    air_density = 1  # kg/m^3

    track = TrackProperties(air_density)

    track.add_critical_point(0, 10, track.FREE_ACCELERATION)
    track.add_critical_point(10, 5, track.FREE_ACCELERATION)
    track.add_critical_point(2000, 100, track.FREE_ACCELERATION)
    track.generate_track_list(segment_distance)

    car = ElectricCarProperties(mass=mass, rotational_inertia=rotational_inertia,
                                motor_power=battery_power, motor_efficiency=motor_efficiency,
                                battery_capacity=10, drag_coefficient=drag_coefficient,
                                frontal_area=frontal_area, wheel_radius=wheel_radius)

    # 1. generate results
    racing_results = racing_simulation(data_store, car, track, main_window)

    # 3. display results
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
