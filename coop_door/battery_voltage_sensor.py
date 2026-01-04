""" Voltage reading on resistor divider. """
import logging
from machine import ADC, Pin # pylint: disable=import-error
from .timer import Timer

logger = logging.getLogger(__name__)

class BatteryVoltageSensor():
    """ Read the voltage and provide new reading notification. """
    def __init__(self, pin_num):
        self.slots = []
        pin = Pin(pin_num)
        self.adc = ADC(pin)
        self.r_up_ohm = 15e3
        self.r_down_ohm = 5e3
        # Only to filter hight frequency noise, there is a already huge cap on battery
        # already. And battery inself is kind of capacitor.
        c_f = 10e-9
        self.adc_max = 65535
        self.vcc_v = 3.2
        init_delay_ms = round(1000 * c_f * self.r_up_ohm * 5)
        self.init_timer = Timer(init_delay_ms, None, Timer.SINGLE_SHOT)
        self.init_timer.start()

    def read(self):
        """ Read the battery voltage
        Perform the ADC reading and return the voltage in
        Volts. Return None first init_delay_ms milliseconds
        to let the input settle (charge caps).
        """
        if self.init_timer.active():
            return None
        adc = self.adc.read_u16()
        v = ((self.r_up_ohm + self.r_down_ohm) * adc * self.vcc_v)\
            / (self.r_down_ohm * self.adc_max)

        for slot in self.slots:
            slot(v)
        return v

    def register_slot(self, slot):
        """ Register voltage slot
        A callback to provide a new voltage reading.
        """
        self.slots.append(slot)
