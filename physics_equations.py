# Physics Equations Pertaining to Racing
# USE ONLY SI UNITS
from math import sqrt
import logging

logger = logging.getLogger(__name__)

GRAVITY = 9.81  # m/s^2


class PhysicsCalculationOutput():
    """Class that contains the data
    that every physics based function must return
    when doing a calculation over one segment of the track.

    This includes:
      - Initial velocity (meters/second)
      - Final velocity (meters/second)
      - distance traveled (meters)
      - time of segment (seconds)
      - energy differential of battery (joules)
      - maybe other things later
    TODO: add checks on output data
    """
    def __init__(self, initial_velocity, final_velocity, distance_traveled,
                 time_of_segment, energy_differential_of_motor, acceleration):
        self.initial_velocity = initial_velocity
        self.final_velocity = final_velocity
        self.distance_traveled = distance_traveled
        self.time_of_segment = time_of_segment
        self.energy_differential_of_motor = energy_differential_of_motor
        self.acceleration = acceleration
        self.motor_power = self.energy_differential_of_motor / self.time_of_segment
        self.battery_power = self.motor_power
        self.battery_energy = self.energy_differential_of_motor


def rotational_inertia_calculation(rotational_mass, effective_radius):
    rotational_inertia = rotational_mass * (effective_radius ** 2)
    logger.debug("rotational inertia, {}, rot mass, {}, effective radius, {}"
                 .format(rotational_inertia, rotational_mass, effective_radius),
                 extra={'sim_index': 'N/A'})
    return rotational_inertia


# Copied from here: https://en.wikipedia.org/wiki/Drag_(physics)
def drag_force_calculation(coefficient_drag, velocity, air_density, frontal_area):
    drag_force = 0.5*air_density*(velocity ** 2) * coefficient_drag * frontal_area
    logger.debug("drag force, {}, air_density, {}, velocity, {}, coef of drag, {}, frontal area, {}"
                 .format(drag_force, air_density, velocity, coefficient_drag, frontal_area),
                 extra={'sim_index': 'N/A'})
    return drag_force


def rolling_resistance_force_calculation(mass_kg, velocity_m_s, tire_press_bar):
    """Calculation of the rolling resistance due to tire friction.
    Reference:
    https://www.engineeringtoolbox.com/rolling-friction-resistance-d_1303.html
    https://en.wikipedia.org/wiki/Rolling_resistance

    Args:
        mass_kg (float): mass of car in kg
        tire_pressure_bar (float): pressure in tires in bar
        velocity (float): velocity of car in m/s

    Returns:
        rolling_resistance_force_newton (float): force of rolling resistance in newtons

    Note that the reference equation gives speed in km/h so a conversion is necessary
    """
    velocity_km_h = velocity_m_s / 3.6  # 1000 m per km,  3600 sec per hr
    coefficient_rolling_resistance = \
        (0.005 + (1/tire_press_bar) * (0.01 + 0.0095 * (velocity_km_h/100) ** 2))
    rolling_resistance_force_newton = coefficient_rolling_resistance * mass_kg * GRAVITY
    logger.debug("rolling_resistance calc, mass, {}, v, {}, tire_press, {}, force, {}"
                 .format(mass_kg, velocity_m_s, tire_press_bar, rolling_resistance_force_newton))
    return rolling_resistance_force_newton


# Kinetic energy change from velocity_start to velocity_end of and object with mass
def kinetic_energy_change_calculation(velocity_end, velocity_start, mass):
    kinetic_energy_change = 0.5*mass*(velocity_end ** 2 - velocity_start ** 2)
    logger.debug("kinetic energy change, {}, mass, {}, v_end, {}, v_start, {}"
                 .format(kinetic_energy_change, mass, velocity_end, velocity_start),
                 extra={'sim_index': 'N/A'})
    return kinetic_energy_change


def kinetic_energy_calculation(mass, velocity):
    kinetic_energy = 0.5 * mass * (velocity ** 2)
    logger.debug("kinetic energy, {}, mass, {}, velocity, {}"
                 .format(kinetic_energy, mass, velocity),
                 extra={'sim_index': 'N/A'})
    return kinetic_energy


def rotational_kinetic_energy_calculation(rotational_inertia, wheel_radius, velocity):
    rotational_kinetic_energy = 0.5 * rotational_inertia * ((velocity/wheel_radius) ** 2)
    logger.debug(
        "rotation kinetic energy, {}, rotational inertia, {}, velocity, {}, wheel_radius, {}"
        .format(rotational_kinetic_energy, rotational_inertia, velocity, wheel_radius),
        extra={'sim_index': 'N/A'})
    return rotational_kinetic_energy


def time_of_travel_calculation(velocity, distance):
    try:
        time_of_travel = distance / velocity
        logger.debug("time of travel, {}, distance, {}, velocity, {}"
                     .format(time_of_travel, distance, velocity),
                     extra={'sim_index': 'N/A'})
    except ZeroDivisionError:
        logger.error("zero division error velocity: {} distance: {}"
                     .format(velocity, distance),
                     extra={'sim_index': 'N/A'})
        raise ZeroDivisionError
    return time_of_travel

def free_acceleration_calculation(initial_velocity,
                                  distance_of_travel,
                                  motor_power,
                                  motor_efficiency,
                                  wheel_radius,
                                  rotational_inertia,
                                  mass,
                                  drag_coefficient,
                                  frontal_area,
                                  wheel_pressure_bar,
                                  air_density):
    """Solve for final velocity using an energy balance.
    THIS MUST BE DONE OVER A SMALL distance_of_travel TO
    MAKE THE ASSUMPTIONS TRUE:
    Assumptions:
        - Drag force calculated using initial velocity
          because change in velocity is assumed to be small
        - No elevation change

    TODO: add in elevation change to equations
    TODO: add in other drag losses to equations

    Elements included:
        - Initial and final kinetic energy
        - Initial and final rotational kinetic energy
        - Drag energy
        - Motor efficiency

    See the e lemons google drive for proof of physics equations

    Args:
        initial_velocity (float): initial velocity of car (meters/second)
        distance_of_travel (float): distance overwhich the car travels (meters)
        motor_power (float): power output (or input) by motor (Watts)
        motor_efficiency (float): efficiency of motor (unitless)
        wheel_radius (float): radius of wheels on car (meters)
        rotational_inertia (float): car's rotational_inertia (kg*m^2)
        mass (float): mass of car (kg)
        drag_coefficient (float): coefficient of drag of car (unitless)
        frontal_area (float): frontal area of car (meters^2)
        wheel_pressure_bar (float): wheel pressure (bar)
        air_density (float): density of air car is travling through (kg/meters^3)

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

    rolling_resistance_force = \
        rolling_resistance_force_calculation(mass, initial_velocity, wheel_pressure_bar)
    rolling_resistance_energy = rolling_resistance_force * time_of_segment

    final_kinetic_energy_term = 0.5 * (rotational_inertia * ((1/wheel_radius) ** 2) +
                                       mass)
    # TODO: change signs to be correct in each individual term (drag forces are negative) and update signs here
    energy_sum = (initial_linear_kinetic_energy +
                  initial_rotational_kinetic_energy -
                  drag_energy -
                  rolling_resistance_energy +
                  energy_motor)
    final_velocity = sqrt(energy_sum /
                          final_kinetic_energy_term)

    final_linear_kinetic_energy = kinetic_energy_calculation(mass, final_velocity)
    final_rotational_kinetic_energy = \
        rotational_kinetic_energy_calculation(rotational_inertia, wheel_radius, final_velocity)

    # TODO MH Add in a check that the actual drag losses
    # using the final velocity wouldn't be XX percent
    # different than the calculated one, if it would be
    # then redo calc with smaller distance traveled
    # or solve with a system of equations

    # time_of_segment = distance_of_travel / ((final_velocity + initial_velocity) / 2)
    acceleration = (final_velocity - initial_velocity) / time_of_segment

    logger.debug("acc, {}, final_v, {}, initial_v, {}, time, {}, distance, {}"
                 .format(acceleration, final_velocity, initial_velocity,
                         time_of_segment, distance_of_travel),
                 extra={'sim_index': 'N/A'})
    logger.debug("final linear e, {}, init linear e, {}, final rot e, {}, init rot e, {}"
                 .format(final_linear_kinetic_energy, initial_linear_kinetic_energy,
                         final_rotational_kinetic_energy, initial_rotational_kinetic_energy),
                 extra={'sim_index': 'N/A'})

    physics_results = PhysicsCalculationOutput(initial_velocity, final_velocity, distance_of_travel,
                                               time_of_segment, energy_motor, acceleration)

    return physics_results


def reverse_dececceleration_calculation(final_velocity,
                                        distance_of_travel,
                                        motor_power,
                                        motor_efficiency,
                                        wheel_radius,
                                        rotational_inertia,
                                        mass,
                                        drag_coefficient,
                                        frontal_area,
                                        wheel_pressure_bar,
                                        air_density):
    """Solve for initial velocity using an energy balance.
    THIS MUST BE DONE OVER A SMALL distance_of_travel TO
    MAKE THE ASSUMPTIONS TRUE:
    Assumptions:
        - Drag force calculated using final velocity
          because change in velocity is assumed to be small
        - No elevation change

    TODO: add in elevation change to equations
    TODO: add in other drag losses to equations

    Elements included:
        - Initial and final kinetic energy
        - Initial and final rotational kinetic energy
        - Drag energy
        - Motor efficiency

    See the e lemons google drive for proof of physics equations

    Args:
        final_velocity (float): final velocity of car (meters/second)
        distance_of_travel (float): distance overwhich the car travels (meters)
        motor_power (float): power output (or input) by motor (Watts)
        motor_efficiency (float): efficiency of motor (unitless)
        wheel_radius (float): radius of wheels on car (meters)
        rotational_inertia (float): car's rotational_inertia (kg*m^2)
        mass (float): mass of car (kg)
        drag_coefficient (float): coefficient of drag of car (unitless)
        frontal_area (float): frontal area of car (meters^2)
        wheel_pressure_bar (float): wheel pressure (bar)
        air_density (float): density of air car is travling through (kg/meters^3)

    Returns:
        output (PhysicsCalculationOutput): output data of the segment
    """

    time_of_segment = time_of_travel_calculation(final_velocity, distance_of_travel)

    energy_motor = motor_power * time_of_segment

    final_linear_kinetic_energy = kinetic_energy_calculation(mass, final_velocity)
    final_rotational_kinetic_energy \
        = rotational_kinetic_energy_calculation(rotational_inertia,
                                                wheel_radius,
                                                final_velocity)
    drag_energy = distance_of_travel * drag_force_calculation(drag_coefficient,
                                                                   final_velocity,
                                                                   air_density,
                                                                   frontal_area)
    # -1 to reverse sign of this force because the simulation is running backwards in time
    rolling_resistance_force = \
        rolling_resistance_force_calculation(mass, final_velocity, wheel_pressure_bar)
    rolling_resistance_energy = rolling_resistance_force * time_of_segment

    initial_kinetic_energy_term = 0.5 * (rotational_inertia * ((1/wheel_radius) ** 2) +
                                         mass)

    energy_sum = (final_linear_kinetic_energy
                  + final_rotational_kinetic_energy
                  - drag_energy
                  - rolling_resistance_energy
                  - energy_motor)
    initial_velocity = sqrt(energy_sum /
                            initial_kinetic_energy_term)

    initial_linear_kinetic_energy = kinetic_energy_calculation(mass, final_velocity)
    initial_rotational_kinetic_energy = \
        rotational_kinetic_energy_calculation(rotational_inertia, wheel_radius, final_velocity)

    # TODO MH Add in a check that the actual drag losses
    # using the final velocity wouldn't be XX percent
    # different than the calculated one, if it would be
    # then redo calc with smaller distance traveled
    # or solve with a system of equations

    # time_of_segment = distance_of_travel / ((final_velocity + initial_velocity) / 2)
    acceleration = (final_velocity - initial_velocity) / time_of_segment

    logger.debug("acc, {}, final_v, {}, initial_v, {}, time, {}, distance, {}"
                 .format(acceleration, final_velocity, initial_velocity,
                         time_of_segment, distance_of_travel),
                 extra={'sim_index': 'N/A'})
    logger.debug("final linear e, {}, init linear e, {}, final rot e, {}, init rot e, {}\n"
                 .format(final_linear_kinetic_energy, initial_linear_kinetic_energy,
                         final_rotational_kinetic_energy, initial_rotational_kinetic_energy),
                 extra={'sim_index': 'N/A'})

    physics_results = PhysicsCalculationOutput(initial_velocity, final_velocity, distance_of_travel,
                                               time_of_segment, energy_motor, acceleration)

    # developer check
    if final_velocity > initial_velocity:
        raise("reverse physics calculation wrong! initial velocity lower than final velocity")

    return physics_results


def constrained_velocity_calculation(initial_velocity,
                                     final_velocity,
                                     distance_of_travel,
                                     motor_efficiency,
                                     rotational_inertia,
                                     mass,
                                     wheel_radius,
                                     drag_coefficient,
                                     frontal_area,
                                     wheel_pressure_bar,
                                     air_density):
    """Calculate amount of energy used over a distance if the
    velocity of the car is constrained.
    TODO: if the velocity constraint results in a violation of some other
    physical parameters then change to a different type of calculation or
    raise an error

    Assumptions:
        - No change in elevation

    Args:
        initial_velocity (float): initial velocity of car in the segment (meters/second)
        final_velocity (float): final velocity of the car in the segment (meters/second)
        distance_of_travel (float): distance overwhich the car travels (meters)
        motor_efficiency (float): efficiency of motor (unitless)
        rotational_inertia (float): car's rotational_inertia (kg*m^2)
        mass (float): mass of car (kg)
        wheel_radius (float): radius of wheels on car (meters)
        drag_coefficient (float): coefficient of drag of car (unitless)
        frontal_area (float): frontal area of car (meters^2)
        wheel_pressure_bar (float): pressure of tires (bar)
        air_density (float): density of air car is travling through (kg/meters^3)

    Returns:
        output (PhysicsCalculationOutput): output data of the segment

    Raises:
        (TODO) Some sort of error if the velocity constraints cannot be met
    """

    time_of_segment = distance_of_travel / ((final_velocity + initial_velocity) / 2)

    acceleration = (final_velocity - initial_velocity) / time_of_segment
    # TODO: change signs to be correct in each individual term (drag forces are negative)
    drag_force = drag_force_calculation(drag_coefficient,
                                        initial_velocity,
                                        air_density,
                                        frontal_area)
    drag_energy = drag_force * distance_of_travel

    rolling_resistance_force = \
        rolling_resistance_force_calculation(mass, initial_velocity, wheel_pressure_bar)
    rolling_resistance_energy = rolling_resistance_force * time_of_segment

    initial_linear_kinetic_energy = kinetic_energy_calculation(mass, initial_velocity)
    initial_rotational_kinetic_energy = \
        rotational_kinetic_energy_calculation(rotational_inertia, wheel_radius, initial_velocity)

    final_linear_kinetic_energy = kinetic_energy_calculation(mass, final_velocity)
    final_rotational_kinetic_energy = \
        rotational_kinetic_energy_calculation(rotational_inertia, wheel_radius, final_velocity)

    energy_motor = (final_rotational_kinetic_energy + final_linear_kinetic_energy -
                    initial_rotational_kinetic_energy - initial_linear_kinetic_energy
                    + drag_energy + rolling_resistance_energy)

    logger.debug("acc, {}, final_v, {}, initial_v, {}, time, {}, distance, {}"
                 .format(acceleration, final_velocity, initial_velocity,
                         time_of_segment, distance_of_travel),
                 extra={'sim_index': 'N/A'})
    logger.debug("final linear e, {}, init linear e, {}, final rot e, {}, init rot e, {}"
                 .format(final_linear_kinetic_energy, initial_linear_kinetic_energy,
                         final_rotational_kinetic_energy, initial_rotational_kinetic_energy),
                 extra={'sim_index': 'N/A'})

    physics_results = PhysicsCalculationOutput(initial_velocity, final_velocity, distance_of_travel,
                                               time_of_segment, energy_motor, acceleration)

    return physics_results


def reverse_max_negative_power_physics_simulation(final_velocity,
                                                  distance_of_travel,
                                                  car,
                                                  air_density):
    """Function that calculats a small portion of a lap of a car with
    car_characteristics on a track with track_characteristics. The
    calculation is done knowing the final velocity and the initial
    velocity is calculated.

    Args:
        final_velocity (float): final velocity (m/s)
        distance_of_travel (float): distance traveled for the calculation
        car (dict): Characteristics of car being simulated
        air_density: density of air that the car is traveling through

    Returns:
        results (ReverseSimulationResults): results of the simulation increment

    """
    results = reverse_dececceleration_calculation(final_velocity,
                                                  distance_of_travel,
                                                  -car["motor_power"],
                                                  car["motor_efficiency"],
                                                  car["wheel_radius"],
                                                  car["rotational_inertia"],
                                                  car["mass"],
                                                  car["drag_coefficient"],
                                                  car["frontal_area"],
                                                  car["wheel_pressure_bar"],
                                                  air_density)
    return results


def max_positive_power_physics_simulation(initial_velocity,
                                          distance_of_travel,
                                          car,
                                          air_density):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics. The
    car is applying maximum foward effort with the motor.

    Args:
        initial_velocity (float): initial velocity (m/s)
        distance_of_travel (float): distance traveled for the calculation
        car (dict): Characteristics of car being simulated
        track (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  results of the simulation at index 'index'

    """
    logger.debug("Max Positive Power Calculation",
                 extra={'sim_index': 'N/A'})
    results = free_acceleration_calculation(initial_velocity,
                                            distance_of_travel,
                                            car["motor_power"],
                                            car["motor_efficiency"],
                                            car["wheel_radius"],
                                            car["rotational_inertia"],
                                            car["mass"],
                                            car["drag_coefficient"],
                                            car["frontal_area"],
                                            car["wheel_pressure_bar"],
                                            air_density)
    return results


def max_negative_power_physics_simulation(initial_velocity,
                                          distance_of_travel,
                                          car,
                                          air_density):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics. The
    car is applying maximum braking effort with the motor.

    Args:
        initial_velocity (float): initial velocity (m/s)
        distance_of_travel (float): distance traveled for the calculation
        car (dict): Characteristics of car being simulated
        track (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  results of the simulation at index 'index'

    """
    logger.debug("",
                 extra={'sim_index': 'N/A'})
    results = free_acceleration_calculation(initial_velocity,
                                            distance_of_travel,
                                            -car["motor_power"],
                                            car["motor_efficiency"],
                                            car["wheel_radius"],
                                            car["rotational_inertia"],
                                            car["mass"],
                                            car["drag_coefficient"],
                                            car["frontal_area"],
                                            car["wheel_pressure_bar"],
                                            air_density)
    return results


def constrained_velocity_physics_simulation(initial_velocity,
                                            final_velocity,
                                            distance_of_travel,
                                            car,
                                            air_density):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics.
    For this method of simulation the car is on a constrained velocity profile

    The strategy of this calculation is a middle reimann sum
        - Drag energy is calculated using the average of initial and final velocity

    Args:
        initial_velocity (float): initial velocity (m/s)
        final_velocity (float): initial velocity (m/s)
        car_properties (dict): Characteristics of car being simulated
        track_properites (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  results of the simulation at index 'index'

    """
    logger.debug("",
                 extra={'sim_index': 'N/A'})
    results = constrained_velocity_calculation(initial_velocity,
                                               final_velocity,
                                               distance_of_travel,
                                               car["motor_efficiency"],
                                               car["rotational_inertia"],
                                               car["mass"],
                                               car["wheel_radius"],
                                               car["drag_coefficient"],
                                               car["frontal_area"],
                                               car["wheel_pressure_bar"],
                                               air_density)
    return results
