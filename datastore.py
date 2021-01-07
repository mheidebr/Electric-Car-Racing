"""Location to store data for the system."""
import logging
import threading
import track_properties
import electric_car_properties
from copy import deepcopy
from PyQt5.QtCore import *

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

        self._lock = QReadWriteLock()

        # for interrupting and stopping the simulation
        self.exit_event = threading.Event()

    # Getters and setters for simulation time variables
    def get_simulation_index(self):
        self._lock.lockForRead()
        logger.debug("index retrieved",
                     extra={'sim_index': self._simulation_index})
        temp = deepcopy(self._simulation_index)
        self._lock.unlock()
        return temp

    def get_walk_back_counter(self):
        self._lock.lockForRead()
        temp = deepcopy(self._walk_back_counter)
        self._lock.unlock()
        return temp

    def increment_simulation_index(self):
        self._lock.lockForWrite()
        temp = self._simulation_index
        self._simulation_index += 1
        logger.debug("index updated to {}".format(self._simulation_index),
                     extra={'sim_index': temp})
        self._lock.unlock()

    def decrement_simulation_index(self):
        self._lock.lockForWrite()
        if self._simulation_index > 0:
            temp = self._simulation_index
            self._simulation_index -= 1
            logger.debug("index updated to {} from {}".format(self._simulation_index,
                                                              temp))
            # index must be more than or equal to 0
        else:
            logger.warning("index at {} and decremented, not allowed"
                           .format(self._simulation_index))
        self._lock.unlock()

    def increment_walk_back_counter(self):
        self._lock.lockForWrite()
        temp = self._walk_back_counter
        self._walk_back_counter += 1
        logger.debug("walk_back_counter updated to {} from {}"
                     .format(self._walk_back_counter, temp),
                     extra={'sim_index': "N/A"})
        self._lock.unlock()

    def reset_walk_back_counter(self):
        self._lock.lockForWrite()
        temp = self._walk_back_counter
        self._walk_back_counter = 0
        logger.info("walk_back_counter updated to {} from {}"
                    .format(self._walk_back_counter, temp),
                    extra={'sim_index': "N/A"})
        self._lock.unlock()

    # getters and setters for simulation related classes
    def get_car_properties(self):
        self._lock.lockForRead()
        temp = deepcopy(self._car.get_car_parameters())
        self._lock.unlock()
        return temp

    def get_track_properties(self):
        self._lock.lockForRead()
        temp = deepcopy(self._track_properties)
        self._lock.unlock()
        return temp

    def get_race_results(self):
        self._lock.lockForRead()
        temp = deepcopy(self._race_simulation_results)
        self._lock.unlock()
        return temp

    def set_car_properties(self, car_properties):
        self._lock.lockForWrite()
        self._car = car_properties
        self._lock.unlock()

    def set_track_properties(self, track_properties):
        self._lock.lockForWrite()
        self._track_properties = track_properties
        self._lock.unlock()

    def set_race_results(self, race_results):
        self._lock.lockForWrite()
        self._race_simulation_results = race_results
        self._lock.unlock()

    # Getters and setters for the lap_results because there is much more
    # interaction with this class during the simulation and doing a copy of the data
    # modifying and then setting it would be very intensive
    def get_lap_results(self):
        self._lock.lockForRead()
        temp = deepcopy(self._lap_simulation_results)
        self._lock.unlock()
        return temp

    def get_time_at_index(self, index):
        self._lock.lockForRead()
        try:
            _time = self._lap_simulation_results.time_list[index]
        except IndexError:
            logger.info("index out of range: {}, returning last time",
                    extra={'sim_index':index})
            _time = self._lap_simulation_results.time_list[-1]
        temp = deepcopy(_time)
        self._lock.unlock()
        return temp

    def get_time_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _time = self._lap_simulation_results.time_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last time",
                    extra={'sim_index':num_index_samples})
            _time = self._lap_simulation_results.time_list
        temp = deepcopy(_time)
        self._lock.unlock()
        return temp

    def get_velocity_at_index(self, index):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.velocity_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last velocity",
                    extra={'sim_index':index})
            _velocity = self._lap_simulation_results.velocity_list[-1]
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    def get_velocity_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.velocity_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last velocity",
                    extra={'sim_index':num_index_samples})
            _velocity = self._lap_simulation_results.velocity_list
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    def get_acceleration_at_index(self, index):
        self._lock.lockForRead()
        try:
            _acceleration = self._lap_simulation_results.acceleration_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last acceleration",
                    extra={'sim_index':index})
            _acceleration = self._lap_simulation_results.acceleration_list[-1]
        temp = deepcopy(_acceleration)
        self._lock.unlock()
        return temp

    def get_acceleration_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _acceleration = self._lap_simulation_results.acceleration_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last acceleration",
                    extra={'sim_index':num_index_samples})
            _acceleration = self._lap_simulation_results.acceleration_list
        temp = deepcopy(_acceleration)
        self._lock.unlock()
        return temp

    def get_distance_at_index(self, index):
        self._lock.lockForRead()
        try:
            _distance = self._lap_simulation_results.distance_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last distance",
                    extra={'sim_index':index})
            _distance = self._lap_simulation_results.distance_list[-1]
        temp = deepcopy(_distance)
        self._lock.unlock()
        return temp

    def get_distance_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _distance = self._lap_simulation_results.distance_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last distance",
                    extra={'sim_index':num_index_samples})
            _distance = self._lap_simulation_results.distance_list
        temp = deepcopy(_distance)
        self._lock.unlock()
        return temp

    def get_battery_power_at_index(self, index):
        self._lock.lockForRead()
        try:
            _battery_power = self._lap_simulation_results.battery_power_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_power",
                    extra={'sim_index':index})
            _battery_power = self._lap_simulation_results.battery_power_list[-1]
        temp = deepcopy(_battery_power)
        self._lock.unlock()
        return temp

    def get_battery_power_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _battery_power = self._lap_simulation_results.battery_power_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_power",
                    extra={'sim_index':num_index_samples})
            _battery_power = self._lap_simulation_results.battery_power_list
        temp = deepcopy(_battery_power)
        self._lock.unlock()
        return temp

    def get_battery_energy_at_index(self, index):
        self._lock.lockForRead()
        try:
            _battery_energy = self._lap_simulation_results.battery_energy_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_energy",
                    extra={'sim_index':index})
            _battery_energy = self._lap_simulation_results.battery_energy_list[-1]
        temp = deepcopy(_battery_energy)
        self._lock.unlock()
        return temp

    def get_battery_energy_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _battery_energy = self._lap_simulation_results.battery_energy_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_energy",
                    extra={'sim_index':num_index_samples})
            _battery_energy = self._lap_simulation_results.battery_energy_list
        temp = deepcopy(_battery_energy)
        self._lock.unlock()
        return temp

    def get_motor_power_at_index(self, index):
        self._lock.lockForRead()
        try:
            _motor_power = self._lap_simulation_results.motor_power_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last motor_power",
                    extra={'sim_index':index})
            _motor_power = self._lap_simulation_results.motor_power_list[-1]
        temp = deepcopy(_motor_power)
        self._lock.unlock()
        return temp

    def get_motor_power_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _motor_power = self._lap_simulation_results.motor_power_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last motor_power",
                    extra={'sim_index':num_index_samples})
            _motor_power = self._lap_simulation_results.motor_power_list
        temp = deepcopy(_motor_power)
        self._lock.unlock()
        return temp

    def get_track_max_velocity_at_index(self, index):
        self._lock.lockForRead()
        try:
            _max_velocity = self._track_properties.max_velocity_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last max_velocity",
                    extra={'sim_index':index})
            _max_velocity = self._track_properties.max_velocity_list[-1]
        temp = deepcopy(_max_velocity)
        self._lock.unlock()
        return temp

    def get_track_max_velocity_list(self, num_index_samples):
        """copy/get a list of num_index_sample track properties maximum velocities values 
        from the max_velocity_list starting at the beginning of the (index=0) 

        Args:
            num_index_samples (int): the number of values to return from the 
            track.max_velocity_list

        """
        self._lock.lockForRead()
        try:
            _max_velocity = self._track_properties.max_velocity_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last max_velocity",
                    extra={'sim_index':num_index_samples})
            _max_velocity = self._track_properties.max_velocity_list
        temp = deepcopy(_max_velocity)
        self._lock.unlock()
        return temp

    def initialize_lap_lists(self, length):
        self._lock.lockForWrite()
        self._lap_simulation_results.initialize_lists(length)
        self._lock.unlock()

    def add_physics_results_to_lap_results(self, physics_results, index):
        self._lock.lockForWrite()
        self._lap_simulation_results.add_physics_results(physics_results, index)
        self._lock.unlock()


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
        self.time_list = []
        self.distance_list = []
        self.motor_power_list = []
        self.battery_power_list = []
        self.battery_energy_list = []
        self.acceleration_list = []
        self.velocity_list = []
        self.physics_results_profile = []

    def initialize_lists(self, length):
        """Function to initialize the profile lists after after
        the initialization of the datastore.
        """

        self.time_list = []
        self.distance_list = []
        self.motor_power_list = []
        self.battery_power_list = []
        self.motor_energy_list = []
        self.acceleration_list = []
        self.velocity_list = []
        self.physics_results_profile = []

        # length - 1 is for the because the first element is added above
        for i in range(length):
            self.time_list.append(0)
            self.distance_list.append(0)
            self.motor_power_list.append(0)
            self.battery_power_list.append(0)
            self.motor_energy_list.append(0)
            self.acceleration_list.append(0)
            self.velocity_list.append(1)
            self.physics_results_profile.append(0)

    def add_physics_results(self, physics_results, index):
        """Function that inserts physics results at index: index
        into the result arrays

        Args:
            physics_results (PhysicsResults): physics results to be inserted into results arrays
            index (int): index at which the physics results should be inserted

        """
        self.physics_results_profile[index] = physics_results

        self.distance_list[index] = (self.distance_list[index - 1] +
                                     physics_results.distance_traveled)
        self.time_list[index] = (self.time_list[index - 1] +
                                 physics_results.time_of_segment)
        self.motor_power_list[index] = physics_results.motor_power
        self.motor_energy_list[index] = (self.motor_energy_list[index - 1] +
                                         physics_results.energy_differential_of_motor)
        self.acceleration_list[index] = physics_results.acceleration
        self.velocity_list[index] = physics_results.final_velocity
