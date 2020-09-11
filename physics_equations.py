# Physics Equations Pertaining to Racing


# Copied from here: https://en.wikipedia.org/wiki/Drag_(physics)
def drag_force(coefficient_drag, velocity, air_density, frontal_area):
    return 0.5*air_density*(velocity ** 2) * coefficient_drag * frontal_area


# Kinetic energy change from velocity_start to velocity_end of and object with mass
def kinetic_energy_change(velocity_end, velocity_start, mass):
    return 0.5*mass*(velocity_end ** 2 - velocity_start ** 2)
