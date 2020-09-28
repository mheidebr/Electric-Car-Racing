#! /usr/bin/python3


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

    """
    def __init__(self, velocity_list, distance_list, lap_time, air_density):
        self.velocity_list = velocity_list
        self.distance_list = distance_list
        self.lap_time = lap_time
        self.air_density = air_density

    def add_critical_point(distance_from_start_finish, type, value)
        this function must accept the critical point and put it in a list
        in the correct distance position (must sort)
        type = type of critical point (max velocity or turn radius)
        value = value with type "type" for the critical point

def generate_track_list(track_properties: TrackProperties, delta_distance):
    """Function for generating a list that represents the track properties
    and car constraints at every delta_distance interval around the track.

    Args:
        track_properties (TrackProperties): A list of critical track points
        delta_distance (double): distance interval at which to generate the list (meters)
    
    Returns:
        track_list (tuple): tuple that contains all track properties and car constraints
            at each delta distance inverval over the entire track 
            TODO: needs concrete definition
    
    Raises:
        Nothing
    """

    This needs to start at 0 distance, increment at delta distance and make a tuple
    that has all the track characteristics in it. It looks at the critical points
    in the list. It assumes that the critical points are in distance order


    return track_list


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
