"""Location to store data for the system."""
import logging
import threading
import track_properties
import electric_car_properties
from copy import deepcopy
from PyQt5.QtCore import QReadWriteLock

from physics_equations import PhysicsCalculationOutput

logger = logging.getLogger(__name__)


class DataResultsUpdate:
    """ convenience class used to pass (retrieve) calculated sim data from DataStore to consumers
    """
    def __init__(self):
        self.refresh_index  # starting index where data retrieved from following respective lists
        self.time_list_update = []
        self.distance_list_update = []
        self.velocity_list_update = []
        self.acceleration_list_update = []
        self.motor_power_list_update = []
        self.battery_power_list_update = []
        self.motor_energy_list_update = []


class DataStore:
    """Handles storage of data for the system, access is thread safe.
    Variables in the datastore should be treated as private and accessed/modified
    with getters and setters.

    For the big data lists, the data at index i represents the data going between the distance
    at index i and the distance at index (i + 1)
    """
    def __init__(self):

        self._car = electric_car_properties.ElectricCarProperties()
        self._track_properties = track_properties.TrackProperties()
        self._lap_simulation_results = LapVelocitySimulationResults()
        self._race_simulation_results = RacingSimulationResults()

        # simulation time variables for managing the simulation index-based data arrays
        # for adding or re-reading data that has been refreshed
        self._simulation_index = 0
        self._walk_back_counter = 0
        self._refresh_index = 0  # indicates starting, lower bound index for consumers (plotRefresh)

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
        logger.debug(
            "walk_back_counter updated to {} from {}".format(self._walk_back_counter, temp),
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
                        extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _time = self._lap_simulation_results.time_list
        temp = deepcopy(_time)
        self._lock.unlock()
        return temp

    def get_time_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _time = self._lap_simulation_results.time_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last time",
                         extra={'sim_index': end_index})
            _time = self._lap_simulation_results.time_list[-1]
        temp = deepcopy(_time)
        self._lock.unlock()
        return temp

    # Use this get for display purposes only
    def get_velocity_at_index_for_display(self, index):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.velocity_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last velocity",
                         extra={'sim_index': index})
            _velocity = self._lap_simulation_results.velocity_list[-1]
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    # The following 2 getters for velocity are to be used by the simulation
    # and access the physics simulation results instead of the velocity
    # list so thet there is less confusion when doing physics calculations
    # back in time or forward in time
    def get_final_velocity_at_index(self, index):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.physics_results_profile[index].final_velocity
        except IndexError:
            logger.error("index out of range: {}, returning last velocity",
                         extra={'sim_index': index})
            _velocity = self._lap_simulation_results.physics_results_profile[-1].final_velocity
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    def get_initial_velocity_at_index(self, index):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.physics_results_profile[index].initial_velocity
        except IndexError:
            logger.error("index out of range: {}, returning first velocity",
                         extra={'sim_index': index})
            _velocity = self._lap_simulation_results.physics_results_profile[0].initial_velocity
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    def get_velocity_list(self, num_index_samples):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.velocity_list[0:num_index_samples]
        except IndexError:
            logger.error("index out of range: {}, returning last velocity",
                         extra={'sim_index': num_index_samples})
            _velocity = self._lap_simulation_results.velocity_list
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    def get_velocity_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _velocity = self._lap_simulation_results.velocity_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last velocity",
                         extra={'sim_index': end_index})
            _velocity = self._lap_simulation_results.velocity_list[-1]
        temp = deepcopy(_velocity)
        self._lock.unlock()
        return temp

    def get_new_data_values(self):
        """ return a dictionary the new refresh_index and all simulation computed lists with
        their updated values from _refresh_index to _simulation_index and update _refresh_index
        to the _simulation_index to indicate the all refreshed data was collected by the consumer.
        We only copy upto _simulation_index-1 because the simulation results may not
        be complete for values at _simulation_index

        Returns:
            tmp_rfi- the index value in the data array where new data was appended
                     This could have been earlier in the array, thereby overwriting
                      previously reported data, and not just appending data to the array
            tmp_vel - the list of newly added data since the last time here.
            tmp_dst - same as above
            tmp_vel - same as above
            tmp_max - same as above
            tmp_acc - same as above
            tmp_mp - same as above
            tmp_bp - same as above
            tmp_be - same as above
        """
        self._lock.lockForWrite()
        try:
            _time = self._lap_simulation_results.time_list[self._refresh_index:
                                                           self._simulation_index-1]
            tmp_time = deepcopy(_time)

            _distance = self._lap_simulation_results.distance_list[self._refresh_index:
                                                                   self._simulation_index-1]
            tmp_dst = deepcopy(_distance)

            _velocity = self._lap_simulation_results.velocity_list[self._refresh_index:
                                                                   self._simulation_index-1]
            tmp_vel = deepcopy(_velocity)

            _max_velocity = self._track_properties.max_velocity_list[self._refresh_index:
                                                                     self._simulation_index-1]
            tmp_max = deepcopy(_max_velocity)

            _acceleration = self._lap_simulation_results.acceleration_list[self._refresh_index:
                                                                           self._simulation_index-1]
            tmp_acc = deepcopy(_acceleration)

            _motor_power = self._lap_simulation_results.motor_power_list[self._refresh_index:
                                                                         self._simulation_index-1]
            tmp_mp = deepcopy(_motor_power)

            _battery_power = self._lap_simulation_results.battery_power_list[
                self._refresh_index: self._simulation_index-1]
            tmp_bp = deepcopy(_battery_power)

            _battery_energy = self._lap_simulation_results.battery_energy_list[
                self._refresh_index: self._simulation_index-1]
            tmp_be = deepcopy(_battery_energy)
        except IndexError:
            logger.error("index out of range: {}, returning empty list",
                         extra={'sim_index': self._refresh_index})
            tmp_time = []
            tmp_dst = []
            tmp_vel = []
            tmp_max = []
            tmp_acc = []
            tmp_mp = []
            tmp_bp = []
            tmp_be = []

        # report the first index where the data got added and/or replaced
        tmp_rfi = self._refresh_index

        # remember how far in the array we copied up to data and passed to the consumer
        self._refresh_index = self._simulation_index-1
        self._lock.unlock()
        newResults = {'refresh_index': tmp_rfi,
                      'time': tmp_time,
                      'distance': tmp_dst,
                      'velocity': tmp_vel,
                      'max_velocity': tmp_max,
                      'acceleration': tmp_acc,
                      'motor_power': tmp_mp,
                      'battery_power': tmp_bp,
                      'battery_energy': tmp_be}
        return newResults

    def set_refresh_index(self, new_refresh_index):
        """ Since the walk back worked, we want to move the index to indicate
        how far the walkback went so that consumers (MainWindow thread PlotRefresh)
        of the data arrays can pick up the newly calculationed data
        from _refresh_index to _simulation_index
        Note: SimulationThread should only move _refresh_index backwards while the consumer
        (MainWindow thread ) should only move it forward while retrieving the new data
        (as enforced "atomically" in get_new_velocity values)

        Args :
            new_refresh_index  -  the index to all data arrays where to start reading data
        """
        self._lock.lockForWrite()
        # ensure the new index is only moving backwards
        if new_refresh_index < self._simulation_index and new_refresh_index < self._refresh_index:
            self._refresh_index = new_refresh_index
        self._lock.unlock()
        return

    def get_acceleration_at_index(self, index):
        self._lock.lockForRead()
        try:
            _acceleration = self._lap_simulation_results.acceleration_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last acceleration",
                         extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _acceleration = self._lap_simulation_results.acceleration_list[-1]
        temp = deepcopy(_acceleration)
        self._lock.unlock()
        return temp

    def get_acceleration_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _acceleration = self._lap_simulation_results.acceleration_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last acceleration",
                         extra={'sim_index': end_index})
            _acceleration = self._lap_simulation_results.acceleration_list[-1]
        temp = deepcopy(_acceleration)
        self._lock.unlock()
        return temp

    def get_distance_at_index(self, index):
        self._lock.lockForRead()
        try:
            _distance = self._lap_simulation_results.distance_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last distance",
                         extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _distance = self._lap_simulation_results.distance_list[-1]
        temp = deepcopy(_distance)
        self._lock.unlock()
        return temp

    def get_distance_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _distance = self._lap_simulation_results.distance_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last distance",
                         extra={'sim_index': end_index})
            _distance = self._lap_simulation_results.distance_list[-1]
        temp = deepcopy(_distance)
        self._lock.unlock()
        return temp

    def get_battery_power_at_index(self, index):
        self._lock.lockForRead()
        try:
            _battery_power = self._lap_simulation_results.battery_power_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_power",
                         extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _battery_power = self._lap_simulation_results.battery_power_list
        temp = deepcopy(_battery_power)
        self._lock.unlock()
        return temp

    def get_battery_power_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _battery_power = self._lap_simulation_results.battery_power_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_power",
                         extra={'sim_index': end_index})
            _battery_power = self._lap_simulation_results.battery_power_list[-1]
        temp = deepcopy(_battery_power)
        self._lock.unlock()
        return temp

    def get_battery_energy_at_index(self, index):
        self._lock.lockForRead()
        try:
            _battery_energy = self._lap_simulation_results.battery_energy_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_energy",
                         extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _battery_energy = self._lap_simulation_results.battery_energy_list[-1]
        temp = deepcopy(_battery_energy)
        self._lock.unlock()
        return temp

    def get_battery_energy_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _battery_energy = self._lap_simulation_results.battery_energy_list[
                begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last battery_energy",
                         extra={'sim_index': end_index})
            _battery_energy = self._lap_simulation_results.battery_energy_list[-1]
        temp = deepcopy(_battery_energy)
        self._lock.unlock()
        return temp

    def get_motor_power_at_index(self, index):
        self._lock.lockForRead()
        try:
            _motor_power = self._lap_simulation_results.motor_power_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last motor_power",
                         extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _motor_power = self._lap_simulation_results.motor_power_list[-1]
        temp = deepcopy(_motor_power)
        self._lock.unlock()
        return temp

    def get_motor_power_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _motor_power = self._lap_simulation_results.motor_power_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last motor_power",
                         extra={'sim_index': end_index})
            _motor_power = self._lap_simulation_results.motor_power_list[-1]
        temp = deepcopy(_motor_power)
        self._lock.unlock()
        return temp

    def get_track_max_velocity_at_index(self, index):
        self._lock.lockForRead()
        try:
            _max_velocity = self._track_properties.max_velocity_list[index]
        except IndexError:
            logger.error("index out of range: {}, returning last max_velocity",
                         extra={'sim_index': index})
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
                         extra={'sim_index': num_index_samples})
            _max_velocity = self._track_properties.max_velocity_list
        temp = deepcopy(_max_velocity)
        self._lock.unlock()
        return temp

    def get_track_max_velocity_in_range(self, begin_index, end_index):
        self._lock.lockForRead()
        try:
            _max_velocity = self._track_properties.max_velocity_list[begin_index:end_index]
        except IndexError:
            logger.error("index out of range: {}, returning last max_velocity",
                         extra={'sim_index': end_index})
            _max_velocity = self._track_properties.max_velocity_list[-1]
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

        physics_result_filler = PhysicsCalculationOutput(1, 1, 1, 1, 1, 1)

        # length - 1 is for the because the first element is added above
        for i in range(length):
            self.time_list.append(0)
            self.distance_list.append(0)
            self.motor_power_list.append(0)
            self.battery_power_list.append(0)
            self.motor_energy_list.append(0)
            self.acceleration_list.append(0)
            self.velocity_list.append(0)
            self.physics_results_profile.append(physics_result_filler)

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
