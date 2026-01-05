""" End switch """
import logging
import machine # pylint: disable=import-error
from machine import Pin # pylint: disable=import-error

logger = logging.getLogger(__name__)

class EndSwitch:
    """ Read and report end switch state.
    Read the state of a switch hooked up to a gpio pin.
    Call a user slot on switch state change.
    """
    def __init__(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.pin.irq(handler=self._irq_handler, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.last_state = None
        self.slots = []

    def is_on(self):
        """ Return True if end switch is active (closed). """
        return not self.pin.value()

    def read(self):
        """ Perform end switch reading. """
        for slot in self.slots:
            if self.is_on() is not self.last_state:
                logger.debug('end switch@%s = %s', self.pin, self.is_on())
                slot(self.is_on())
        self.last_state = self.is_on()

    def register_slot(self, slot):
        """ Register a slot to report switch state change. """
        self.slots.append(slot)

    def _irq_handler(self, _pin):
        irq_enabled = machine.disable_irq()
        self.read()
        machine.enable_irq(irq_enabled)
