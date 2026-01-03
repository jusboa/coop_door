import math

class Filter:
    def __init__(self, k):
        self.reset()
        self.k = k

    def output(self):
        return self.y

    def sample(self, x):
        if math.isnan(self.y):
            self.y = x
        else:
            # y(n) = y(n - 1) + k * (x(n) - y(n - 1))
            self.y = self.y + self.k * (x - self.y)
        return self.y

    def set_coefficient(self, k):
        self.k = k

    def coefficient(self):
        return self.k

    def reset(self):
        self.y = math.nan
