"""Location to store data for the system."""
import logging
import threading
import track_properties
import electric_car_properties
from copy import deepcopy

logger = logging.getLogger(__name__)


class DataStore:
    """Handles storage of data for the system, access is thread safe.
    Variables in the datastore should be treated as private and accessed/modified
    with getters and setters
    """

    def __init__(self):

        self._car = electric_car_properties.ElectricCarProperties()
        self._track_properties = track_properties.TrackProperties()
        self._lap_simulation_results = LapVelocitySimulationResults()
        self._race_simulation_results = RacingSimulationResults()

        # simulation time variables
        self._simulation_index = 1
        self._walk_back_counter = 0

        self._car_lock = threading.Lock()
        self._track_properties_lock = threading.Lock()
        self._lap_simulation_results_lock = threading.Lock()
        self._race_simulation_results_lock = threading.Lock()
        self._simulation_info_lock = threading.Lock()  # lock for simulation time variables

        # for interrupting and stopping the simulation
        self.exit_event = threading.Event()

    # Getters and setters for simulation time variables
    def get_simulation_index(self):
        with self._simulation_info_lock:
            logger.debug("index retrieved",
                         extra={'sim_index': self._simulation_index})
            return deepcopy(self._simulation_index)

    def get_walk_back_counter(self):
        with self._simulation_info_lock:
            return deepcopy(self._walk_back_counter)

    def increment_simulation_index(self):
        with self._simulation_info_lock:
            temp = self._simulation_index
            self._simulation_index += 1
            logger.debug("index updated to {}".format(self._simulation_index),
                         extra={'sim_index': temp})

    def decrement_simulation_index(self):
        with self._simulation_info_lock:
            if self._simulation_index > 0:
                temp = self._simulation_index
                self._simulation_index -= 1
                logger.debug("index updated to {} from {}".format(self._simulation_index,
                                                                  temp))
            # index must be more than or equal to 0
            else:
                logger.warning("index at {} and decremented, not allowed"
                               .format(self._simulation_index))

    def increment_walk_back_counter(self):
        with self._simulation_info_lock:
            temp = self._walk_back_counter
            self._walk_back_counter += 1
            logger.debug("walk_back_counter updated to {} from {}".format(self._walk_back_counter,
                                                                          temp))

    def reset_walk_back_counter(self):
        with self._simulation_info_lock:
            temp = self._walk_back_counter
            self._walk_back_counter = 1
            logger.debug("walk_back_counter updated to {} from {}".format(self._walk_back_counter,
                                                                          temp))

    # getters and setters for simulation related classes
    def get_car_properties(self):
        with self._car_lock:
            return self._car.get_car_parameters()

    def get_track_properties(self):
        with self._track_properties_lock:
            return deepcopy(self._track_properties)

    def get_race_results(self):
        with self._race_simulation_results_lock:
            return self._race_simulation_results

    def set_car_properties(self, car_properties):
        with self._car_lock:
            self._car = car_properties

    def set_track_properties(self, track_properties):
        with self._track_properties_lock:
            self._track_properties = track_properties

    def set_race_results(self, race_results):
        with self._race_simulation_results_lock:
            self._race_simulation_results = race_results

    # Getters and setters for the lap_results because there is much more
    # interaction with this class during the simulation and doing a copy of the data
    # modifying and then setting it would be very intensive
    def get_lap_results(self):
        with self._lap_simulation_results_lock:
            return self._lap_simulation_results

    def get_velocity_at_index(self, index):
        with self._lap_simulation_results_lock:
            try:
                velocity = self._lap_simulation_results.velocity_profile[index]
            except IndexError:
                logger.info("index out of range: {}, returning last velocity")
                velocity = self._lap_simulation_results.velocity_profile[-1]
        return velocity

    def initialize_lap_profiles(self, length):
        with self._lap_simulation_results_lock:
            self._lap_simulation_results.initialize_profiles(length)

    def add_physics_results_to_lap_results(self, physics_results, index):
        with self._lap_simulation_results_lock:
            self._lap_simulation_results.add_physics_results(physics_results, index)


class RacingSimulationResults():
    def __init__(self):
        self.laps_per_pit_stop = 0
        self.lap_time = 0
        self.lap_results = 0


class LapVelocitySimulationResults():
    def __init__(self):
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

    def initialize_profiles(self, length):
        """Function to initialize the profile lists after after
        the initialization of the datastore.
        """

        self.time_profile = []
        self.distance_profile = []
        self.motor_power_profile = []
        self.battery_power_profile = []
        self.motor_energy_profile = []
        self.acceleration_profile = []
        self.velocity_profile = []
        self.physics_results_list = []

        # lenght - 1 is for the because the first element is added above
        for i in range(length):
            self.time_profile.append(0)
            self.distance_profile.append(0)
            self.motor_power_profile.append(0)
            self.battery_power_profile.append(0)
            self.motor_energy_profile.append(0)
            self.acceleration_profile.append(0)
            self.velocity_profile.append(1)
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
        self.motor_energy_profile[index] = (self.motor_energy_profile[index - 1] +
                                            physics_results.energy_differential_of_motor)
        self.acceleration_profile[index] = physics_results.acceleration
        self.velocity_profile[index] = physics_results.final_velocity
