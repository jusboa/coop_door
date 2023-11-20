from machine import Pin

class Motor():
    def __init__(self, gpio0, gpio1):
        self.pin0_value = 0
        self.pin1_value = 0
        self.drive_pin0 = Pin(gpio0, Pin.OUT)
        self.drive_pin1 = Pin(gpio1, Pin.OUT)

    def _drive(self):
        self.drive_pin0.value(self.pin0_value)
        self.drive_pin1.value(self.pin1_value)

    def forward(self):
        self.pin0_value = 1
        self.pin1_value = 0
        self._drive()

    def backward(self):
        self.pin0_value = 0
        self.pin1_value = 1
        self._drive()

    def stop(self):
        self.pin0_value = 0
        self.pin1_value = 0
        self._drive()

    def direction(self):
        if (self.pin0_value == 1
            and self.pin1_value == 0):
            return 1
        elif (self.pin0_value == 0
              and self.pin1_value == 1):
            return -1
        elif (self.is_off()):
            return 0

    def is_off(self):
        return (self.pin0_value
                == self.pin1_value)
