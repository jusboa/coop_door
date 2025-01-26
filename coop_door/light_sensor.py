from machine import ADC, Pin

class LightSensor():
    def __init__(self, adc_channel, en_pin):
        self.slots = []
        self.adc = ADC(adc_channel);
        self.R_UP_OHM = 10e3
        self.R_DARK_OHM = 0.5e6
        self.R_LIGHT_OHM = 25e3
        self.R_HYSTERESIS_OHM = 2e3
        self.ADC_MAX = 65535
        self.day_night_threshold_ohm = self.R_LIGHT_OHM
        self.light = 0
        self.was_day = None
        self._is_day = None
        self.en_pin = Pin(en_pin, Pin.OUT)

    def read_light_intensity(self):
        """ Return the light intensity in %.
        Perform the ADC reading and return the light
        intensity in percents (0% - dark, 100% - full light).
        The function is blocking.
        """
        self.en_pin.value(1)
        adc_sensor = self.adc.read_u16()
        #print(f'adc={adc_sensor}')
        self.en_pin.value(0)
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

        #print(f'R = {self.r_sensor / 1000:.2f} kOhm')
        #print(f'day = {self._is_day}')
        if (self.was_day is not self._is_day):
            self.was_day = self._is_day
            for slot in self.slots:
                slot(self._is_day)

        return self.is_day()

    def is_day(self):
        return self._is_day

    def register_light_slot(self, slot):
        self.slots.append(slot)
