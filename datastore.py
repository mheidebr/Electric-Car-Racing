"""Location to store data for the system."""
import logging
import threading

logger = logging.getLogger(__name__)


class DataStore:
    """Handles storage of data for the system, access is thread safe.
    Variables in the datastore should be treated as private and accessed/modified
    with getters and setters
    """

    def __init__(self):

        self.cars = []
        self.tracks = []

        # index to do the simulations
        self._simulation_index = 0
        self._walk_back_counter = 0
        self._velocity = 1

        self._simulation_index_lock = threading.Lock()
        self._walk_back_counter_lock = threading.Lock()
        self._velocity_lock = threading.Lock()

    def get_simulation_index(self):
        with self._simulation_index_lock:
            return self._simulation_index

    def get_velocity(self):
        with self._velocity_lock:
            return self._velocity

    def get_walk_back_counter(self):
        with self._walk_back_counter_lock:
            return self._walk_back_counter

    def increment_simulation_index(self):
        with self._simulation_index_lock:
            temp = self._simulation_index
            self._simulation_index += 1
            logger.debug("index updated to {} from {}".format(self._simulation_index,
                                                            temp))

    def decrement_simulation_index(self):
        with self._simulation_index_lock:
            if self._simulation_index < 0:
                temp = self._simulation_index
                self._simulation_index -= 1
                logger.debug("index updated to {} from {}".format(self._simulation_index,
                                                                temp))
            # index must be more than or equal to 0
            else:
                logger.warning("index at {} and decremented, not allowed".format(self._simulation_index))

    def increment_walk_back_counter(self):
        with self._walk_back_counter_lock:
            temp = self._walk_back_counter
            self._walk_back_counter += 1
            logger.debug("walk_back_counter updated to {} from {}".format(self._walk_back_counter,
                                                                        temp))

    def reset_walk_back_counter(self):
        with self._walk_back_counter_lock:
            temp = self._walk_back_counter
            self._walk_back_counter = 1
            logger.debug("walk_back_counter updated to {} from {}".format(self._walk_back_counter,
                                                                        temp))

    def set_velocity(self, new_velocity):
        if new_velocity >= 0:
            with self._velocity_lock:
                temp = self._velocity
                self._velocity = new_velocity
                logger.debug("velocity updated to {} from {}".format(self._velocity,
                                                                    temp))
        else:
            logger.warning("invalid new_velocity input, must be > 0: {}".format(new_velocity))


class RacingSimulationResults():
    def __init__(self):
        self.laps_per_pit_stop = 0
        self.lap_time = 0

        self.lap_results = 0


class LapVelocitySimulationResults():
    def __init__(self, length, main_window):
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

        self.main_window = main_window

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
        self.time_profile[index] = (self.time_profile[index - 1] +
                                    physics_results.time_of_segment)
        self.motor_power_profile[index] = physics_results.motor_power
        self.battery_power_profile[index] = (physics_results.energy_differential_of_battery /
                                             physics_results.time_of_segment)
        self.battery_energy_profile[index] = (self.battery_energy_profile[index - 1] +
                                              physics_results.energy_differential_of_battery)
        self.acceleration_profile[index] = physics_results.acceleration
        self.velocity_profile[index] = physics_results.final_velocity
        print("Physics Results")
        print(physics_simulation)

        print("time_profile: {}".format(self.time_profile[index]))
        print("distance_profile: {}".format(self.distance_profile[index]))
        print("battery_energy_profile: {}".format(self.battery_energy_profile[index]))
        time.sleep(0.5)

        self.main_window.regraph(self.time_profile, self.distance_profile, self.velocity_profile)