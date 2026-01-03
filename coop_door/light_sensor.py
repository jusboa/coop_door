from machine import ADC, Pin
from .timer import Timer
import logging

logger = logging.getLogger(__name__)

class LightSensor():
    def __init__(self, adc_pin_num, en_pin):
        self.slots = []
        adc_pin = Pin(adc_pin_num)
        self.adc = ADC(adc_pin);
        self.R_UP_OHM = 10e3
        self.R_DARK_OHM = 0.5e6
        self.R_LIGHT_OHM = 70e3
        self.R_HYSTERESIS_OHM = 4e3
        self.C_F = 4.7e-6
        self.ADC_MAX = 65535
        self.day_night_threshold_ohm = self.R_LIGHT_OHM
        self.light = 0
        self._is_day = None
        self.en_pin = Pin(en_pin, Pin.OUT)
        self.WAKEUP_DELAY_MS = 50 * round(1000 * self.C_F * self.R_UP_OHM * 5 / 50)
        self.wakeup_timer = Timer(self.WAKEUP_DELAY_MS, None, Timer.SINGLE_SHOT)

    def read(self):
        """ Return the light intensity in %.
        Perform the ADC reading and return the light
        intensity in percents (0% - dark, 100% - full light).
        The function is blocking.
        """
        if self.wakeup_timer.active():
            return
        adc_sensor = self.adc.read_u16()
        #logger.debug(f'adc={adc_sensor}')
        if (adc_sensor >= self.ADC_MAX):
            self.r_sensor = self.R_DARK_OHM
        else:
            self.r_sensor = adc_sensor * self.R_UP_OHM / (self.ADC_MAX - adc_sensor)

        if self.r_sensor < 0:
            self.r_sensor = 0

        if self.r_sensor <= self.day_night_threshold_ohm:
            self._is_day = True
            self.day_night_threshold_ohm = self.R_LIGHT_OHM + self.R_HYSTERESIS_OHM
        else:
            self._is_day = False
            self.day_night_threshold_ohm = self.R_LIGHT_OHM - self.R_HYSTERESIS_OHM

        #logger.debug(f'R = {self.r_sensor / 1000:.2f} kOhm')
        #logger.debug(f'day = {self._is_day}')
        for slot in self.slots:
            slot(self._is_day)

    def wakeup(self):
        self.en_pin.value(1)
        self.wakeup_timer.start()

    def sleep(self):
        self.en_pin.value(0)

    def is_day(self):
        return self._is_day

    def register_light_slot(self, slot):
        self.slots.append(slot)
