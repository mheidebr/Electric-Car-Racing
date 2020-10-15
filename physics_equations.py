# Physics Equations Pertaining to Racing
# USE ONLY SI UNITS
from math import sqrt
from electric_car_properties import ElectricCarProperties
from track_properties import TrackProperties
import logging

logger = logging.getLogger(__name__)

class PhysicsCalculationOutput():
    """Class that contains the data
    that every physics based function must return
    when doing a calculation over one segment of the track.

    This includes:
      - Final velocity (meters/second)
      - distance traveled (meters)
      - time of segment (seconds)
      - energy differential of battery (joules)
      - maybe other things later
    TODO: add checks on output data
    """
    def __init__(self, final_velocity, distance_traveled, time_of_segment,
                 energy_differential_of_battery, acceleration):
        self.final_velocity = final_velocity
        self.distance_traveled = distance_traveled
        self.time_of_segment = time_of_segment
        self.energy_differential_of_battery = energy_differential_of_battery
        self.acceleration = acceleration


def rotational_inertia_calculation(rotational_mass, effective_radius):
    return rotational_mass * (effective_radius ** 2)


# Copied from here: https://en.wikipedia.org/wiki/Drag_(physics)
def drag_force_calculation(coefficient_drag, velocity, air_density, frontal_area):
    return 0.5*air_density*(velocity ** 2) * coefficient_drag * frontal_area


# Kinetic energy change from velocity_start to velocity_end of and object with mass
def kinetic_energy_change(velocity_end, velocity_start, mass):
    return 0.5*mass*(velocity_end ** 2 - velocity_start ** 2)


def kinetic_energy_calculation(mass, velocity):
    return 0.5 * mass * (velocity ** 2)


def rotational_kinetic_energy_calculation(rotational_inertia, wheel_radius, velocity):
    return 0.5 * rotational_inertia * ((velocity/wheel_radius) ** 2)


def time_of_travel_calculation(velocity, distance):
    print("time of travel calc, distance, velocity: {} {}".format(distance, velocity))
    return distance / velocity


def free_acceleration_calculation(initial_velocity,
                                  distance_of_travel,
                                  motor_power,
                                  motor_efficiency,
                                  wheel_radius,
                                  rotational_inertia,
                                  mass,
                                  drag_coefficient,
                                  frontal_area,
                                  air_density):
    """Solve for final velocity using an energy balance.
    THIS MUST BE DONE OVER A SMALL distance_of_travel TO
    MAKE THE ASSUMPTIONS TRUE:
    Assumptions:
        - Drag force calculated using initial velocity because change in velocity is assumed to be small
        - No elevation change

    TODO: add in elevation change to equations
    TODO: add in other drag losses to equations

    Elements included:
        - Initial and final kinetic energy
        - Initial and final rotational kinetic energy
        - Drag energy
        - Motor efficiency

    See <somewhere-else> for proof of physics equations

    Args:
        initial_velocity (double): initial velocity of car (meters/second)
        distance_of_travel (double): distance overwhich the car travels (meters)
        motor_power (double): power output (or input) by motor (Watts)
        motor_efficiency (double): efficiency of motor (unitless)
        wheel_radius (double): radius of wheels on car (meters)
        rotational_inertia (double): car's rotational_inertia (kg*m^2)
        mass (double): mass of car (kg)
        drag_coefficient (double): coefficient of drag of car (unitless)
        frontal_area (double): frontal area of car (meters^2)
        air_density (double): density of air car is travling through (kg/meters^3)

    Returns:
        output (PhysicsCalculationOutput): output data of the segment
    """

    time_of_segment = time_of_travel_calculation(initial_velocity, distance_of_travel)

    energy_motor = motor_power * time_of_segment

    # TODO: add in rolling resistance
    initial_linear_kinetic_energy = kinetic_energy_calculation(mass, initial_velocity)
    initial_rotational_kinetic_energy \
        = rotational_kinetic_energy_calculation(rotational_inertia,
                                                wheel_radius,
                                                initial_velocity)
    drag_energy = distance_of_travel * drag_force_calculation(drag_coefficient,
                                                              initial_velocity,
                                                              air_density,
                                                              frontal_area)

    final_kinetic_energy_term = 0.5 * (rotational_inertia * ((1/wheel_radius) ** 2) +
                                       mass)

    energy_sum = (initial_linear_kinetic_energy +
                  initial_rotational_kinetic_energy -
                  drag_energy +
                  energy_motor * motor_efficiency)
    final_velocity = sqrt(energy_sum /
                          final_kinetic_energy_term)

    # TODO MH Add in a check that the actual drag losses using the final velocity wouldn't be XX percent
    # different than the calculated one, if it would be then redo calc with smaller distance traveled
    # or solve with a system of equations

    # time_of_segment = distance_of_travel / ((final_velocity + initial_velocity) / 2)
    acceleration = (final_velocity - initial_velocity) / time_of_segment

    physics_results = PhysicsCalculationOutput(final_velocity, distance_of_travel,
                                               time_of_segment, energy_motor, acceleration)

    return physics_results


def constrained_velocity_calculation(initial_velocity,
                                     final_velocity,
                                     distance_of_travel,
                                     motor_efficiency,
                                     drag_coefficient,
                                     frontal_area,
                                     air_density):
    """Calculate amount of energy used over a distance if the
    velocity of the car is constrained.
    TODO: if the velocity constraint results in a violation of some other
    physical parameters then change to a different type of calculation or
    raise an error

    Assumptions:
        - No change in elevation

    Args:
        initial_velocity (double): initial velocity of car in the segment (meters/second)
        final_velocity (double): final velocity of the car in the segment (meters/second)
        distance_of_travel (double): distance overwhich the car travels (meters)
        motor_efficiency (double): efficiency of motor (unitless)
        drag_coefficient (double): coefficient of drag of car (unitless)
        frontal_area (double): frontal area of car (meters^2)
        air_density (double): density of air car is travling through (kg/meters^3)

    Returns:
        output (PhysicsCalculationOutput): output data of the segment

    Raises:
        (TODO) Some sort of error if the velocity constraints cannot be met
    """
    drag_force = drag_force_calculation(drag_coefficient,
                                        initial_velocity,
                                        air_density,
                                        frontal_area)
    drag_energy = drag_force * distance_of_travel

    final_velocity = final_velocity
    distance_of_travel = distance_of_travel

    time_of_segment = distance_of_travel / ((final_velocity + initial_velocity) / 2)
    energy_motor = drag_energy

    acceleration = (final_velocity - initial_velocity) / time_of_segment

    physics_results = PhysicsCalculationOutput(final_velocity, distance_of_travel,
                                               time_of_segment, energy_motor, acceleration)

    return physics_results


def max_positive_power_physics_simulation(initial_velocity,
                                          distance_of_travel,
                                          car: ElectricCarProperties,
                                          track: TrackProperties):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics. The
    car is applying maximum foward effort with the motor.

    Args:
        initial_velocity (float): initial velocity (m/s)
        distance_of_travel (float): distance traveled for the calculation
        car (ElectricCarProperties): Characteristics of car being simulated
        track (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  results of the simulation at index 'index'

    """
    results = free_acceleration_calculation(initial_velocity,
                                            distance_of_travel,
                                            car.motor_power,
                                            car.motor_efficiency,
                                            car.wheel_radius,
                                            car.rotational_inertia,
                                            car.mass,
                                            car.drag_coefficient,
                                            car.frontal_area,
                                            track.air_density)
    return results


def max_negative_power_physics_simulation(initial_velocity,
                                          distance_of_travel,
                                          car: ElectricCarProperties,
                                          track: TrackProperties):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics. The
    car is applying maximum braking effort with the motor.

    Args:
        initial_velocity (float): initial velocity (m/s)
        distance_of_travel (float): distance traveled for the calculation
        car (ElectricCarProperties): Characteristics of car being simulated
        track (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  results of the simulation at index 'index'

    """
    results = free_acceleration_calculation(initial_velocity,
                                            distance_of_travel,
                                            -car.motor_power,
                                            car.motor_efficiency,
                                            car.wheel_radius,
                                            car.rotational_inertia,
                                            car.mass,
                                            car.drag_coefficient,
                                            car.frontal_area,
                                            track.air_density)
    return results


def constrained_velocity_physics_simulation(initial_velocity,
                                            final_velocity,
                                            distance_of_travel,
                                            car: ElectricCarProperties,
                                            track: TrackProperties):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics.
    For this method of simulation the car is on a constrained velocity profile

    The strategy of this calculation is a middle reimann sum
        - Drag energy is calculated using the average of initial and final velocity

    Args:
        initial_velocity (float): initial velocity (m/s)
        final_velocity (float): initial velocity (m/s)
        car_properties (ElectricCarProperties): Characteristics of car being simulated
        track_properites (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  results of the simulation at index 'index'

    """

    results = constrained_velocity_calculation(initial_velocity,
                                               final_velocity,
                                               distance_of_travel,
                                               car.motor_efficiency,
                                               car.drag_coefficient,
                                               car.frontal_area,
                                               track.air_density)
    return results


# def physics_simulation(initial_velocity,
#                        distance_of_travel,
#                        motor_power,
#                        car: ElectricCarProperties,
#                        track: TrackProperties):
#     """Function that calculates a small portion of a lap
#     of a car with car_characteristics on a track with track_characteristics.

#     The strategy of this calculation is a middle reimann sum
#         - Drag energy is calculated using the average of initial and final velocity

#     Args:
#         initial_velocity (float): initial velocity (m/s)
#         index (float): index in the track lists for the calculation
#         car_properties (ElectricCarProperties): Characteristics of car being simulated
#         track_properites (TrackProperties): Characteristics of track being simulated

#     Returns:
#         results (PysicsSimultaionResults):  results of the simulation at index 'index'

#     """

#     if track.max_velocity_list[index] is track.FREE_ACCELERATION:
#         results = free_acceleration_calculation(initial_velocity,
#                                                 distance_of_travel,
#                                                 car.motor_power,
#                                                 car.motor_efficiency,
#                                                 car.wheel_radius,
#                                                 car.rotational_inertia,
#                                                 car.mass,
#                                                 car.drag_coefficient,
#                                                 car.frontal_area,
#                                                 track.air_density)

#     elif track.max_velocity_list[index] is track.CONSTANT_VELOCITY:
#         results = constrained_velocity_calculation(initial_velocity,
#                                                    initial_velocity,
#                                                    distance_of_travel,
#                                                    car.motor_efficiency,
#                                                    car.drag_coefficient,
#                                                    car.frontal_area,
#                                                    track.air_density)


#     return results
