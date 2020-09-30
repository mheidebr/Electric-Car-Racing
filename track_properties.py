#! /usr/bin/python3

import collections
import numpy


class TrackProperties:
    """Class for holding the critical points of the track.
    A critical point is where a track property changes (turn radius) or
    a car constraint changes (max velocity).

    Class that holds relevant information about the track.
    Critical points list should consist of thses elements:
     - distance from start finish line (meters)
     - max velocity (meters/s)
     - velocity constraint, must be either "none" "linear" or "constant"
     - elevation of the track (meters)
     - width of the track (meters)
     - radius of the track corner (meters) should be 'None' if the track is straight
     - bank of the corner


    The intended use of this class is for the user to input critical points
    that represent the track and then call the generate_track_list function
    which will generate lists used for the simulation.

    THE HIGHEST distance_from_start_finish VALUE IS USED AS THE END
    OF THE TRACK DISTANCE

    """
    def __init__(self, air_density):
        self.air_density = air_density

        self._critical_point_dict = {}

        # lists for using in the simulation later
        self.distance_list = []
        self.velocity_constraint_list = []
        self.max_velocity_list = []

        # Constants
        self.FREE_ACCELERATION = "free"
        self.LINEAR_ACCELERATION = "linear"
        self.CONSTANT_ACCELERATION = "constant"

    def add_critical_point(self, distance_from_start_finish,
                           max_velocity, velocity_constraint):
        """Function that adds points to the critical_point_dict.
        It sorts the critical points by distance from start finish.

        Args:
            distance_from_start_finish (float): distance from the start
                                                finish line of the critical point (meters)
            max_velocity (float): maximum allowable velocity at that point in the track (meters/second)
            velocity_constraint (string): type of velocity constraint, "free" "linear" or "constant"

        Returns:
            Nothing

        Raises:
            Nothing

        """

        self._critical_point_dict[distance_from_start_finish] = (max_velocity,
                                                                 velocity_constraint)

    def generate_track_list(self, delta_distance):
        """Function for generating a list that represents the track properties
        and car constraints at every delta_distance interval around the track.

        Args:
            delta_distance (float): distance interval at which to generate the list (meters)

        Returns:
            Nothing

        Raises:
            Nothing
        """

        ordered_dict = collections.OrderedDict(self._critical_point_dict)

        # This needs to start at 0 distance, increment at delta distance and make a tuple
        # that has all the track characteristics in it. It looks at the critical points
        # in the list. It assumes that the critical points are in distance order

        max_velocity = 0
        velocity_constraint = "free"

        # highest distance value:
        last_distance = next(reversed(ordered_dict))
        print("last distance: {}".format(last_distance))

        for x in numpy.arange(0, last_distance, delta_distance):
            # update the max velocity and velocity constraint
            try:
                max_velocity, velocity_constraint = ordered_dict[x]
            except KeyError:
                pass

            self.distance_list.append(x)
            self.velocity_constraint_list.append(velocity_constraint)
            self.max_velocity_list.append(max_velocity)

# in meters/second
test_track_max_velocity = [
    20,
    23,
    25,
    26,
    28,
    30,
    25,
    20,
    21,
    22,
    22,
    25,
    28,
    32,
    36,
    40,
    42,
    38,
    35,
    32,
    28,
    24,
    20,
]


test_track_distance_list = [
    0,
    100,
    200,
    300,
    400,
    500,
    600,
    700,
    800,
    900,
    1000,
    1100,
    1200,
    1300,
    1400,
    1500,
    1600,
    1700,
    1800,
    1900,
    2000,
    2100,
    2200,
]

test_track_2_distance = [
    0,
    100,
    200
]

test_track_2_max_velocity = [
    10,
    20,
    5,
]
