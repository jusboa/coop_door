from machine import Pin

class Motor():
    def __init__(self, gpio0, gpio1, gpio_en):
        self.pin0_value = 0
        self.pin1_value = 0
        self.drive_pin0 = Pin(gpio0, Pin.OUT)
        self.drive_pin1 = Pin(gpio1, Pin.OUT)
        self.enable_pin = Pin(gpio_en, Pin.OUT)

    def _drive(self):
        self.enable_pin.value(1)
        self.drive_pin0.value(self.pin0_value)
        self.drive_pin1.value(self.pin1_value)
        #print(f'pin0 value = {self.pin0_value}')
        #print(f'pin1 value = {self.pin1_value}')

    def go(self, direction):
        if direction > 0:
            self.pin0_value = 1
            self.pin1_value = 0
        elif direction < 0:
            self.pin0_value = 0
            self.pin1_value = 1
        else:
            # == 0
            self.stop()
        self._drive()

    def backward(self):
        self.pin0_value = 0
        self.pin1_value = 1
        self._drive()

    def stop(self):
        self.pin0_value = 0
        self.pin1_value = 0
        self.drive_pin0.value(self.pin0_value)
        self.drive_pin1.value(self.pin1_value)
        self.enable_pin.value(0)

    def direction(self):
        if (self.pin0_value == 1
            and self.pin1_value == 0):
            return 1
        elif (self.pin0_value == 0
              and self.pin1_value == 1):
            return -1
        elif (not self.is_running()):
            return 0

    def is_running(self):
        return (self.pin0_value
                != self.pin1_value)
