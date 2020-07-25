# All track/winning car properties go here


class TrackProperties:
    def __init__(self, velocity_list, distance_list, lap_time):
        self.velocity_list = velocity_list
        self.distance_list = distance_list
        self.lap_time = lap_time


# in meters/second
test_track_velocity_list = [
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