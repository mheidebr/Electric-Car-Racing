# The actual simulation goes here
# USE ONLY SI UNITS
import sys
import os
from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

from physics_equations import (free_acceleration_calculation,
                               time_of_travel_calculation)
#from electric_car_properties import ElectricCarProperties
#from track_properties import TrackProperties

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


# def racing_simulation(car_properties: ElectricCarProperties,
#                       track_properties: TrackProperties):
#     """Function accepts a car and a track and executes
#     a simulation to ouput critical metrics related
#     to battery life and track speed.

#     Args:
#         car_properties (ElectricCarProperties): Characteristics of car being simulated
#         track_properites (TrackProperties): Characteristics of track being simulated

#     Returns:
#         results (RacingSimulationResults): output of the simulation

#     """
#     results = RacingSimulationResults()

#     output = lap_velocity_simulation(stuff)
#     results = output

#     return results


# def lap_velocity_simulation(initial_velocity,
#                             car_properties: ElectricCarProperties,
#                             track_properties: TrackProperties): # TODO this needs to be the track list not track properties!!
#     """Function calculates the velocity profile of a car with
#     car_properties on a track with track_properties. The car
#     starts with an ititial velocity of initial_velocity.

#     Args:
#         initial_velocity (double): initial velocity of the car at time = 0
#         delta_distance (double): length over which each physics simulation is done
#         car_properties (ElectricCarProperties): Characteristics of car being simulated
#         track_properites (TrackProperties): Characteristics of track being simulated

#     Returns:
#         results (LapVelocitySimulationResults): output of the lap simulation
#     """
#     results = LapVelocitySimulationResults()
#     output = physics_simulation(stuff)

#     results = output (maybe)
#     return results


# def physics_simulation(initial_velocity,
#                        distance_of_travel,
#                        car_properties: ElectricCarProperties,
#                        track_properites: TrackProperties):
#     """Function that calculates a small portion of a lap
#     of a car with car_characteristics on a track with track_characteristics.

#     The strategy of this calculation is a middle reimann sum
#         - Drag energy is calculated using the average of initial and final velocity

#     Args:
#         initial_velocity (double): initial velocity (m/s)
#         distance_of_travle (double): distance over which the car travels for the energy summation (meters)
#         car_properties (ElectricCarProperties): Characteristics of car being simulated
#         track_properites (TrackProperties): Characteristics of track being simulated

#     Returns:
#         results (PysicsSimultaionResults):  output of the lap simulation

#     """
#     results = PysicsSimultaionResults()

#     results.distance_of_segment = distance_of_travel
#     results.time_of_segment = time_of_travel_calculation(initial_velocity, distance_of_travel)
#     results.battery_energy = car_properties.motor_power * results.time_of_segment

#     # Do calculations here
#     results.end_velocity = free_acceleration_calculation(initial_velocity,
#                                                          distance_of_travel,
#                                                          results.battery_energy,
#                                                          car_properties.drag_coefficient,
#                                                          car_properties.wheel_radius,
#                                                          car_properties.rotation_inertia,
#                                                          car_properties.mass,
#                                                          car_properties.coefficient_of_drag,
#                                                          car_properties.frontal_area,
#                                                          track_properites.air_density)

#     results.acceleration = (results.end_velocity - initial_velocity) / results.time_of_segment

#     return results


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, distance, velocity, acceleration, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        # plot data: x, y values
        self.graphWidget.plot(distance, velocity)
        self.graphWidget.plot(distance, acceleration)


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
    coefficient_of_drag = 0.4
    frontal_area = 7  # m^2
    air_density = 1  # kg/m^3

    total_time = 0
    total_distance = 0

    # 1. generate results
    results_list = []
    while (abs(initial_velocity - end_velocity) > 0.0001):
        initial_velocity = end_velocity  # this line must be first in the calculation

        time_of_segment = time_of_travel_calculation(initial_velocity, segment_distance)
        results = free_acceleration_calculation(initial_velocity,
                                                segment_distance,
                                                battery_power*time_of_segment,
                                                motor_efficiency,
                                                wheel_radius,
                                                rotational_inertia,
                                                mass,
                                                coefficient_of_drag,
                                                frontal_area,
                                                air_density)
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
    for results in results_list:
        distance.append(results.distance_traveled + distance[-1])
        acceleration.append(results.acceleration)
        velocity.append(results.final_velocity)

    # 3. display results
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(distance, velocity, acceleration)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
