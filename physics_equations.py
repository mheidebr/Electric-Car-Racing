# Physics Equations Pertaining to Racing
# USE ONLY SI UNITS
from math import sqrt


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
    return distance/velocity


def final_velocity_calculation(initial_velocity,
                               distance_of_travel,
                               energy_battery,
                               motor_efficiency,
                               wheel_radius,
                               rotational_inertia,
                               mass,
                               coefficient_of_drag,
                               frontal_area,
                               air_density,
                               ):
    """Solve for final velocity using an energy balance.
    THIS MUST BE DONE OVER A SMALL distance_of_travel TO
    MAKE THE ASSUMPTIONS TRUE:
    Assumptions:
        - Drag force calculated using initial velocity because change in velocity is assumed to be small
        - No elevation change

    Elements included:
        - Initial and final kinetic energy
        - Initial and final rotational kinetic energy
        - Drag energy
        - Motor efficiency

    See <somewhere-else> for proof of physics equations

    Args:
        initial_velocity (double): initial velocity of car (meters/second)
        distance_of_travel (double): distance overwhich the car travels (meters)
        energy_battery (double): energy consumed or produced by the battery (joules)
        motor_efficiency (double): efficiency of motor (unitless)
        wheel_radius (double): radius of wheels on car (meters)
        rotational_inertia (double): car's rotational_inertia (kg*m^2)
        mass (double): mass of car (kg)
        coefficient_of_drag (double): coefficient of drag of car (unitless)
        frontal_area (double): frontal area of car (meters^2)
        air_density (double): density of air car is travling through (kg/meters^3)

    Returns:
        final_velocity (double): ending velocity for the car in the segment
    """

    initial_linear_kinetic_energy = kinetic_energy_calculation(mass, initial_velocity)
    initial_rotational_kinetic_energy \
        = rotational_kinetic_energy_calculation(rotational_inertia,
                                                wheel_radius,
                                                initial_velocity)
    drag_energy = distance_of_travel * drag_force_calculation(coefficient_of_drag,
                                                              initial_velocity,
                                                              air_density,
                                                              frontal_area)

    final_kinetic_energy_term = 0.5 * (rotational_inertia * ((1/wheel_radius) ** 2) +
                                       mass)

    energy_sum = (initial_linear_kinetic_energy +
                  initial_rotational_kinetic_energy -
                  drag_energy +
                  energy_battery * motor_efficiency)
    final_velocity = sqrt(energy_sum /
                          final_kinetic_energy_term)
    
    # TODO MH Add in a check that the actual drag losses using the final velocity wouldn't be XX percent
    # different than the calculated one, if it would be then redo calc with smaller distance traveled

    return final_velocity


def energy_consumption_constant_velocity(velocity,
                                         distance_of_travel,
                                         motor_efficiency,
                                         coefficient_of_drag,
                                         frontal_area,
                                         air_density):
    """Calculate amount of energy used over a distance if the
    velocity of the car must remain constant.
    The energy consumed by the motor is calculated as the
    energy due to drag forces.
    Assumptions:
        - No change in elevation

    Args:
        velocity (double): velocity of car (meters/second)
        distance_of_travel (double): distance overwhich the car travels (meters)
        motor_efficiency (double): efficiency of motor (unitless)
        coefficient_of_drag (double): coefficient of drag of car (unitless)
        frontal_area (double): frontal area of car (meters^2)
        air_density (double): density of air car is travling through (kg/meters^3)

    Returns:
        energy_battery (double): energy consumed or produced by the battery (joules)
    """

    drag_force = drag_force_calculation(coefficient_of_drag,
                                        velocity,
                                        air_density,
                                        frontal_area)
    drag_energy = drag_force * distance_of_travel
    energy_battery = drag_energy/motor_efficiency

    return energy_battery
