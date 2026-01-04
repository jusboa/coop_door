""" Light sensor based on photeresistor. """
import logging
from machine import ADC, Pin # pylint: disable=import-error
from .timer import Timer

logger = logging.getLogger(__name__)

class LightSensor():
    """ Read light sensor and report light/dark condition.
    Read the resistance of a photoresistor and when a threshold
    is tripped report light/dark condition via a slot.
    """
    R_UP_OHM = 10e3
    R_DARK_OHM = 0.5e6
    R_LIGHT_OHM = 70e3
    R_HYSTERESIS_OHM = 4e3
    C_F = 4.7e-6
    ADC_MAX = 65535
    def __init__(self, adc_pin_num, en_pin):
        self.slots = []
        adc_pin = Pin(adc_pin_num)
        self.adc = ADC(adc_pin)
        self.day_night_threshold_ohm = self.R_LIGHT_OHM
        self._is_day = None
        self.en_pin = Pin(en_pin, Pin.OUT)
        wakeup_delay_ms = 50 * round(1000 * self.C_F * self.R_UP_OHM * 5 / 50)
        self.wakeup_timer = Timer(wakeup_delay_ms, None, Timer.SINGLE_SHOT)
        self.r_sensor = None

    def read(self):
        """ Return the light intensity in %.
        Perform the ADC reading and return the light
        intensity in percents (0% - dark, 100% - full light).
        The function is blocking.
        """
        if self.wakeup_timer.active():
            return
        adc_sensor = self.adc.read_u16()
        if adc_sensor >= self.ADC_MAX:
            self.r_sensor = self.R_DARK_OHM
        else:
            self.r_sensor = adc_sensor * self.R_UP_OHM / (self.ADC_MAX - adc_sensor)

        self.r_sensor = max(self.r_sensor, 0)

        if self.r_sensor <= self.day_night_threshold_ohm:
            self._is_day = True
            self.day_night_threshold_ohm = self.R_LIGHT_OHM + self.R_HYSTERESIS_OHM
        else:
            self._is_day = False
            self.day_night_threshold_ohm = self.R_LIGHT_OHM - self.R_HYSTERESIS_OHM

        for slot in self.slots:
            slot(self._is_day)

    def wakeup(self):
        """ Sample the sensor.
        Wake up to collect a sensor reading
        and evaluate dark/light.
        """
        self.en_pin.value(1)
        self.wakeup_timer.start()

    def sleep(self):
        """ Put the sensot to sleep. """
        self.en_pin.value(0)

    def is_day(self):
        """ Return True on day. """
        return self._is_day

    def register_light_slot(self, slot):
        """ Regiater a slot to report light/dark changes. """
        self.slots.append(slot)
