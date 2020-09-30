# The actual simulation goes here
# USE ONLY SI UNITS
import sys
import os
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

from physics_equations import physics_simulation
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties

def total_power_consumption(car, track):
    for i in range(len(track.distance_list)):
        # placeholder
        return 0


class RacingSimulationResults():
    def __init__(self):
        laps_per_pit_stop = 0
        motor_power_profile = []
        battery_power_profile = []
        acceleration_profile = []
        velocity_profile = []


class LapVelocitySimulationResults():
    def __init__(self):
        end_velocity = 0
        lap_time = 0
        motor_power_profile = []
        battery_power_profile = []
        acceleration_profile = []
        velocity_profile = []


class PysicsSimultaionResults():
    def __init__(self):
        end_velocity = 0
        time_of_segment = 0
        distance_of_segment = 0
        battery_energy = 0
        acceleration = 0


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
                            car_properties: ElectricCarProperties,
                            track_properties: TrackProperties): # TODO this needs to be the track list not track properties!!
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
    results = LapVelocitySimulationResults()
    output = physics_simulation(stuff)

    results = output(maybe)
    return results


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
    initial_velocity = 0  # m/s
    end_velocity = 1
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
    track.add_critical_point(20, 100, track.FREE_ACCELERATION)
    track.generate_track_list(segment_distance)

    car = ElectricCarProperties(mass=mass, rotational_inertia=rotational_inertia,
                                motor_power=battery_power, motor_efficiency=motor_efficiency,
                                battery_capacity=10, drag_coefficient=drag_coefficient,
                                frontal_area=frontal_area, wheel_radius=wheel_radius)

    # 1. generate results
    results_list = []
    for i in range(len(track.distance_list) - 1):
        if i is 0:
            print("i is 0")
        initial_velocity = end_velocity  # this line must be first in the calculation

        results = physics_simulation(initial_velocity, i, car, track)

        # acceleration = (end_velocity - initial_velocity)/time_of_segment
        # total_time = total_time + time_of_segment
        # total_distance = total_time + segment_distance

        # print("v_0: {}, v_1: {}, acc: {}, time: {}, dist: {}".format(initial_velocity,
        #                                                              end_velocity,
        #                                                              acceleration,
        #                                                              total_time,
        #                                                              total_distance))
        end_velocity = results.final_velocity
        results_list.append(results)

    # 2. manipulate results
    distance = [0]
    acceleration = [0]
    velocity = [0]
    time = [0]
    for results in results_list:
        distance.append(results.distance_traveled + distance[-1])
        acceleration.append(results.acceleration)
        velocity.append(results.final_velocity)
        time.append(results.time_of_segment + time[-1])

    # 3. display results
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(distance, velocity, acceleration, time)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
