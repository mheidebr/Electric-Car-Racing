# all electric car properties go here


# Make sure all units match! All units should be SI
class ElectricCarProperties:
    def __init__(self, mass, rotational_inertia, motor_power,
                 battery_capacity, drag_coefficient, frontal_area,
                 wheel_radius):
        if mass <= 0:
            raise Exception("Invalid Mass {}".format(mass))
        elif rotational_inertia <=0:
            raise Exception("Invalid Rotational Inertia {}".format(rotational_inertia))
        elif motor_power <= 0:
            raise Exception("Invalid motor power {}".format(motor_power))
        elif battery_capacity <= 0:
            raise Exception("Invalid battery capacity {}".format(battery_capacity))
        # some assumption with drag coefficient that its not super high
        elif not (0 <= drag_coefficient <= 1):
            raise Exception("Invalid drag coefficient {}".format(drag_coefficient))
        elif frontal_area <= 0:
            raise Exception("Invalid frontal_area {}".format(frontal_area))
        elif wheel_radius <= 0:
            raise Exception("Invalid wheel_radius {}".format(wheel_radius))
        else:
            self.mass = mass
            self.rotational_inertia = rotational_inertia
            self.motor_power = motor_power
            self.battery_capacity = battery_capacity
            self.drag_coefficient = drag_coefficient
            self.frontal_area = frontal_area
            self.wheel_radius = wheel_radius
