import logging

logger = logging.getLogger(__name__)


# Make sure all units match! All units should be SI
class ElectricCarProperties:
    def __init__(self):
        self._properties_set = False
        self._car_parameters = {}

    def set_car_parameters(self, mass, rotational_inertia, motor_power, motor_efficiency,
                           battery_capacity, drag_coefficient, frontal_area,
                           wheel_radius):

        if mass <= 0:
            raise Exception("Invalid Mass {}".format(mass))
        elif rotational_inertia <= 0:
            raise Exception("Invalid Rotational Inertia {}".format(rotational_inertia))
        elif motor_power <= 0:
            raise Exception("Invalid motor power {}".format(motor_power))
        elif not 0 <= motor_efficiency <= 1:
            raise Exception("Invalid motor efficiency {}".format(motor_efficiency))
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
            self._car_parameters["mass"] = mass
            self._car_parameters["rotational_inertia"] = rotational_inertia
            self._car_parameters["motor_power"] = motor_power
            self._car_parameters["motor_efficiency"] = motor_efficiency
            self._car_parameters["battery_capacity"] = battery_capacity
            self._car_parameters["drag_coefficient"] = drag_coefficient
            self._car_parameters["frontal_area"] = frontal_area
            self._car_parameters["frontal_area"] = frontal_area
            self._car_parameters["wheel_radius"] = wheel_radius

            self._properties_set = True

    def get_car_parameters(self):
        if self._properties_set:
            return self._car_parameters
        else:
            logger.error("Properties Not Set Yet!", extra={'sim_index': 'N/A'})
