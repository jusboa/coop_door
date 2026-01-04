""" Exponential average digital filter. """
import math

class Filter:
    """ Sample and filter a given quantity. """
    def __init__(self, k):
        self.y = None
        self.reset()
        self.k = k

    def output(self):
        """ Return the latest filter output. """
        return self.y

    def sample(self, x):
        """ Take a sample and filter it.
        Return the filtered value.
        """
        if math.isnan(self.y):
            self.y = x
        else:
            # y(n) = y(n - 1) + k * (x(n) - y(n - 1))
            self.y = self.y + self.k * (x - self.y)
        return self.y

    def set_coefficient(self, k):
        """ Set the filter coefficient.
        The coeffieint range shall be (0, 1].
        The lower the value the more aggressive filtering.
        k = 1: input = output
        """
        self.k = k

    def coefficient(self):
        """ Return the filter coefficient (0, 1]. """
        return self.k

    def reset(self):
        """ Reset the filter memory.
        Call sample the get a valid filter output, otherwise
        nan is returned.
        """
        self.y = math.nan
