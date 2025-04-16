from machine import ADC, Pin
from .timer import Timer
import logging

logger = logging.getLogger(__name__)

class BatteryVoltageSensor():
    def __init__(self, pin_num):
        self.slots = []
        pin = Pin(pin_num)
        self.adc = ADC(pin)
        self.R_UP_OHM = 15e3
        self.R_DOWN_OHM = 5e3
        # Only to filter hight frequency noise, there is a already huge cap on battery
        # already. And battery inself is kind of capacitor.
        self.C_F = 10e-9
        self.ADC_MAX = 65535
        self.VCC_V = 3.2
        self.INIT_DELAY_MS = round(1000 * self.C_F * self.R_UP_OHM * 5)
        self.init_timer = Timer(self.INIT_DELAY_MS, None, Timer.SINGLE_SHOT)
        self.init_timer.start()

    def read(self):
        """ Read the battery voltage
        Perform the ADC reading and return the voltage in
        Volts. Return None first INIT_DELAY_MS milliseconds
        to let the input settle (charge caps).
        """
        if self.init_timer.active():
            return None
        adc = self.adc.read_u16()
        #logger.debug(f'adc={adc}')
        v = ((self.R_UP_OHM + self.R_DOWN_OHM) * adc * self.VCC_V) / (self.R_DOWN_OHM * self.ADC_MAX)

        for slot in self.slots:
            slot(v)
        return v

    def register_slot(self, slot):
        self.slots.append(slot)
