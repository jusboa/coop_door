import machine
from machine import Pin
import logging

logger = logging.getLogger(__name__)

class EndSwitch:
    def __init__(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.pin.irq(handler=self._irq_handler, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.last_state = None
        self.slots = []

    def is_on(self):
        return not self.pin.value()

    def read(self):
        for slot in self.slots:
            if (self.is_on() is not self.last_state):
                logger.debug(f'end switch@{self.pin} = {self.is_on()}')
                slot(self.is_on())
        self.last_state = self.is_on()

    def register_slot(self, slot):
        self.slots.append(slot)

    def _irq_handler(self, pin):
        irq_enabled = machine.disable_irq()
        self.read()
        machine.enable_irq(irq_enabled)
