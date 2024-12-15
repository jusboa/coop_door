from machine import Pin

class EndSwitch:
    def __init__(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.last_state = None
        self.slots = []

    def is_on(self):
        return not self.pin.value()

    def read(self):
        for slot in self.slots:
            if (self.is_on() is not self.last_state):
                slot(self.is_on())
        self.last_state = self.is_on()

    def register_slot(self, slot):
        self.slots.append(slot)
