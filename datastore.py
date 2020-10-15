"""Location to store data for the system."""
import logging

logger = logging.getLogger(__name__)


class DataStore:
    """Handles storage of data for the system, access is thread safe.
    Variables in the datastore should be treated as private and accessed/modified
    with getters and setters
    """

    def __init__(self):

        self.cars = []
        self.tracks = []

        # index to do the simulations
        self._index = 0
        self._walk_back_counter = 0
        self._velocity = 0

    def get_index(self):
        return self._index

    def get_velocity(self):
        return self._velocity

    def get_walk_back_counter(self):
        return self._walk_back_counter

    def increment_index(self):
        temp = self._index
        self._index += 1
        logger.debug("index updated to {} from {}".format(self._index,
                                                          temp))

    def decrement_index(self):
        if self._index < 0:
            temp = self._index
            self._index -= 1
            logger.debug("index updated to {} from {}".format(self._index,
                                                              temp))
        # index must be more than or equal to 0
        else:
            logger.warning("index at {} and decremented, not allowed".format(self._index))

    def increment_walk_back_counter(self):
        temp = self._walk_back_counter
        self._walk_back_counter += 1
        logger.debug("walk_back_counter updated to {} from {}".format(self._walk_back_counter,
                                                                      temp))

    def reset_walk_back_counter(self):
        temp = self._walk_back_counter
        self._walk_back_counter = 1
        logger.debug("walk_back_counter updated to {} from {}".format(self._walk_back_counter,
                                                                      temp))

    def set_velocity(self, new_velocity):
        if new_velocity >= 0:
            temp = self._velocity
            self._velocity = new_velocity
            logger.debug("velocity updated to {} from {}".format(self._velocity,
                                                                 temp))
        else:
            logger.warning("invalid new_velocity input, must be > 0: {}".format(new_velocity))
