# The actual simulation goes here
# USE ONLY SI UNITS
import sys
import os
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from copy import deepcopy, copy

from physics_equations import (physics_simulation,
                               max_negative_power_physics_simulation,
                               max_positive_power_physics_simulation,
                               constrained_velocity_physics_simulation,
                               )
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties


def total_power_consumption(car, track):
    for i in range(len(track.distance_list)):
        # placeholder
        return 0


class RacingSimulationResults():
    def __init__(self):
        self.laps_per_pit_stop = 0
        self.lap_time = 0

        self.lap_results = LapVelocitySimulationResults()


class LapVelocitySimulationResults():
    def __init__(self, length):
        """Class that contains the results of the simulation
        over one lap. 

        Args:
            length (int): length of output arrays, this should be the 
                          length of the track lists (ex: track.distance_list)
        """
        self.end_velocity = 0
        self.lap_time = 0
        self.time_profile = []
        self.distance_profile = []
        self.motor_power_profile = []
        self.battery_power_profile = []
        self.battery_energy_profile = []
        self.acceleration_profile = []
        self.velocity_profile = []
        self.physics_results_list = []

        for i in range(length):
            self.time_profile.append(0)
            self.distance_profile.append(0)
            self.motor_power_profile.append(0)
            self.battery_power_profile.append(0)
            self.battery_energy_profile.append(0)
            self.acceleration_profile.append(0)
            self.velocity_profile.append(0)
            self.physics_results_list.append(0)

    def add_physics_results(self, physics_results, index):
        """Function that inserts physics results at index: index
        into the result arrays

        Args:
            physics_results (PhysicsResults): physics results to be inserted into results arrays
            index (int): index at which the physics results should be inserted

        """
        self.physics_results_list[index] = physics_results

        self.distance_profile[index] = (self.distance_profile[index - 1] +
                                        physics_results.distance_traveled)
        self.time_profile[index] = (lap_results.time_profile[index - 1] +
                                    physics_results.time_of_segment)
        self.motor_power_profile[index] = physics_results.motor_power
        self.battery_power_profile[index] = 0  # TODO: make this real
        self.battery_energy_profile[index] = physics_results.energy_differential_of_battery  # TODO make this real
        self.acceleration_profile[index] = physics_results.acceleration
        self.velocity_profile[index] = physics_results.final_velocity


def racing_simulation(car: ElectricCarProperties,
                      track: TrackProperties):
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
    lap_results = LapVelocitySimulationResults()

    initial_velocity = 3  # m/s
    final_velocity = 1
    while(abs(initial_velocity - final_velocity) > 1):
        initial_velocity = final_velocity
        lap_results = lap_velocity_simulation(initial_velocity, car, track)
        final_velocity = lap_results.lap_time

    for physics_results in lap_results.physics_results_list:

        results.acceleration_profile.append(physics_results.acceleration)
        results.velocity_profile.append(physics_results.final_velocity)
        results.battery_energy_profile.append(results.battery_energy_profile[-1] +
                                              physics_results.energy_differential_of_battery)

        battery_power = (physics_results.energy_differential_of_battery /
                         physics_results.time_of_segment)
        results.battery_power_profile.append(battery_power)

    results.laps_per_pit_stop = car.battery_capacity / results.battery_energy_profile[-1]
    results.lap_time = lap_results.end_velocity
    results.lap_results = lap_results

    return results


def lap_velocity_simulation(initial_velocity,
                            car: ElectricCarProperties,
                            track: TrackProperties):
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

    lap_results = LapVelocitySimulationResults()

    velocity = copy(initial_velocity)

    for i in range(len(track.distance_list) - 1):
        physics_results = physics_simulation(velocity, i, car, track)

        lap_results.physics_results_list.append(physics_results)

        lap_results.distance_profile.append(lap_results.distance_profile[-1] +
                                            physics_results.distance_traveled)
        lap_results.time_profile.append(lap_results.time_profile[-1] +
                                        physics_results.time_of_segment)
        velocity = physics_results.final_velocity

    lap_results.end_velocity = lap_results.physics_results_list[-1].final_velocity
    lap_results.lap_time = lap_results.time_profile[-1]

    sim_index = 0
    walk_back_index = 1
    # need to populate the time profile be the same length as the distance list
    # to complete a lap of simulation
    while sim_index < len(track.distance_list):
        
        distance_of_travel = (track.distance_list[sim_index + 1] -
                              track.distance_list[sim_index])
        physics_results = max_positive_power_physics_simulation(velocity, distance_of_travel, car, track)

        # check if velocity constraints are violated
        if physics_results.final_velocity > track.max_velocity_list[sim_index]:
            # velocity constraint violated!!
            # start walking back until velocity constraint at sim_index is met
            while lap_results.velocity_profile[sim_index] > track.max_velocity_list[sim_index]:
                for i in range((sim_index - walk_back_index), (sim_index - 1)):
                    velocity = lap_results.velocity_profile[i - 1]
                    # recalculate with negative motor power
                    results = max_negative_power_physics_simulation(velocity,
                                                                    distance_of_travel,
                                                                    car,
                                                                    track)
                    
                    

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
                    walk_back_index += 1
                # recalculate from (sim_index - walk_back_index) to sim_index
                # with max negative power from (sim_index - walk_back_index) to (sim_index - 1)
                # and a constrained velocity calculation at (sim_index)

                # problem, too much motor power!

                # start incrementing back if a velocity constraint is violated
                # and keep doing that until the velocity constraint is not violated

            # reset walk back index
            walk_back_index = 1
        
        
        # back to normal 
        sim_index += 1
        velocity = physics_results.final_velocity
            # continue business as normal
            # do normal things while no constraints are violated
        # add to lap_results here
        lap_results.physics_results_list.append(physics_results)

        lap_results.distance_profile.append(lap_results.distance_profile[-1] +
                                            physics_results.distance_traveled)
        lap_results.time_profile.append(lap_results.time_profile[-1] +
                                        physics_results.time_of_segment)
        # TODO add to other lists:
        # self.motor_power_profile = [0]
        # self.battery_power_profile = [0]
        # self.battery_energy_profile = [0]
        # self.acceleration_profile = [0]
        # self.velocity_profile = [0]


    return lap_results


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, distance, velocity, acceleration, time, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        # plot data: x, y values
        self.graphWidget.plot(time, distance)
        self.graphWidget.plot(time, velocity)


# rotational inertia estimation: http://www.hpwizard.com/rotational-inertia.html
def main():
    initial_velocity = 40  # m/s

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

    track.add_critical_point(0, 100, track.FREE_ACCELERATION)
    track.add_critical_point(10, 50, track.FREE_ACCELERATION)
    track.add_critical_point(2000, 100, track.FREE_ACCELERATION)
    track.generate_track_list(segment_distance)

    car = ElectricCarProperties(mass=mass, rotational_inertia=rotational_inertia,
                                motor_power=battery_power, motor_efficiency=motor_efficiency,
                                battery_capacity=10, drag_coefficient=drag_coefficient,
                                frontal_area=frontal_area, wheel_radius=wheel_radius)

    # 1. generate results
    racing_results = racing_simulation(car, track)

    # 3. display results
    app = QtWidgets.QApplication(sys.argv)
    # main = MainWindow(lap_results.distance_profile, velocity,
    #                   acceleration, lap_results.time_profile)
    main = MainWindow(racing_results.lap_results.distance_profile,
                      racing_results.velocity_profile,
                      racing_results.acceleration_profile,
                      racing_results.lap_results.time_profile)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
