# The actual simulation goes here


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
    def __init__():
        end_velocity = 0
        lap_time = 0
        motor_power_profile = []
        battery_power_profile = []
        acceleration_profile = []
        velocity_profile = []


class PysicsSimultaionResults():
    def __init__():
        end_velocity = 0
        time_of_segment = 0
        distance_of_segment = 0
        motor_energy = 0
        battery_energy = 0


def racing_simulation(car_properties, track_properties):
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


def lap_velocity_simulation(initial_velocity, car_properties, track_properties):
    """Function calculates the velocity profile of a car with
    car_properties on a track with track_properties. The car
    starts with an ititial velocity of initial_velocity.

    Args:
        initial_velocity (double): initial velocity of the car at time = 0
        car_properties (ElectricCarProperties): Characteristics of car being simulated
        track_properites (TrackProperties): Characteristics of track being simulated

    Returns:
        results (LapVelocitySimulationResults): output of the lap simulation
    """
    results = LapVelocitySimulationResults()

    output = physics_simulation(stuff)

    results = output
    return results


def physics_simulation(initial_velocity, car_properties, track_properites):
    """Function that calculates a small portion of a lap
    of a car with car_characteristics on a track with track_characteristics

    Args:
        initial_velocity (double): initial velocity
        car_properties (ElectricCarProperties): Characteristics of car being simulated
        track_properites (TrackProperties): Characteristics of track being simulated

    Returns:
        results (PysicsSimultaionResults):  output of the lap simulation

    """
    results = PysicsSimultaionResults()

    # Do calculations here

    return results
