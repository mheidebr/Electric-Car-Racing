import logging

logger = logging.getLogger(__name__)


# Make sure all units match! All units should be SI
class ElectricCarProperties:
    def __init__(self):
            self._properties_set = False
            self.mass = 0
            self.rotational_inertia = 0
            self.motor_power = 0
            self.motor_efficiency = 0
            self.battery_capacity = 0
            self.drag_coefficient = 0
            self.frontal_area = 0
            self.wheel_radius = 0
        
    def set_car_parameters(self, mass, rotational_inertia, motor_power, motor_efficiency,
                           battery_capacity, drag_coefficient, frontal_area,
                           wheel_radius):
      
        if mass <= 0:
            raise Exception("Invalid Mass {}".format(mass))
        elif rotational_inertia <=0:
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
            self._mass = mass
            self._rotational_inertia = rotational_inertia
            self._motor_power = motor_power
            self._motor_efficiency = motor_efficiency
            self._battery_capacity = battery_capacity
            self._drag_coefficient = drag_coefficient
            self._frontal_area = frontal_area
            self._wheel_radius = wheel_radius
            self._properties_set = True
    
    def get_mass():
        if self._propserties_set:
            return self.mass
        else:
            logger.error("Properties Not Set Yet!",)


