from machine import Pin

class EndSwitch:
    def __init__(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)

    def isOn(self):
        return not self.pin.value()
