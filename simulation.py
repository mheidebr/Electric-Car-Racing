# The actual simulation goes here
# USE ONLY SI UNITS
import sys
import os
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from copy import deepcopy

from physics_equations import physics_simulation
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties

def total_power_consumption(car, track):
    for i in range(len(track.distance_list)):
        # placeholder
        return 0


class RacingSimulationResults():
    def __init__(self):
        self.laps_per_pit_stop = 0
        self.motor_power_profile = []
        self.battery_power_profile = []
        self.acceleration_profile = []
        self.velocity_profile = []


class LapVelocitySimulationResults():
    def __init__(self):
        self.end_velocity = 0
        self.lap_time = 0
        self.time_profile = [0]
        self.distance_profile = [0]

        self.physics_results_list = []


def racing_simulation(car_properties: ElectricCarProperties,
                      track_properties: TrackProperties):
    """Function accepts a car and a track and executes
    a simulation to ouput critical metrics related
    to battery life and track speed.

    Args:
        car_properties (ElectricCarProperties): Characteristics of car being simulated
        track_properites (TrackProperties): Characteristics of track being simulated

    Returns:
        results (RacingSimulationResults): output of the simulation

    """
    results = RacingSimulationResults()

    output = lap_velocity_simulation(stuff)
    results = output

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
        car_properties (ElectricCarProperties): Characteristics of car being simulated
        track_properites (TrackProperties): Characteristics of track being simulated

    Returns:
        results (LapVelocitySimulationResults): output of the lap simulation
    """

    lap_results = LapVelocitySimulationResults()

    # Deepcopy because dumb
    velocity = deepcopy(initial_velocity)

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

    return lap_results


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, distance, velocity, acceleration, time, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        # plot data: x, y values
        # self.graphWidget.plot(time, distance)
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
    lap_results = lap_velocity_simulation(initial_velocity, car, track)

    # 2. manipulate results
    acceleration = [0]
    velocity = [initial_velocity]
    for physics_results in lap_results.physics_results_list:

        acceleration.append(physics_results.acceleration)
        velocity.append(physics_results.final_velocity)

    # 3. display results
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(lap_results.distance_profile, velocity,
                      acceleration, lap_results.time_profile)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
