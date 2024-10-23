from machine import ADC

class LightSensor():
    def __init__(self, adc_channel):
        self.slots = []
        self.adc = ADC(adc_channel);
        self.R_UP_OHM = 3.3e3
        self.R_DARK_OHM = 20e6
        self.R_LIGHT_OHM = 190
        self.ADC_MAX = 65535
        self.DAY_LIGHT_PCT = 50
        self.DAY_HYSTERESIS_PCT = 10
        self.day_night_threshold_pct = self.DAY_LIGHT_PCT
        self.light = 0
        self.was_day = None

    def read_light_intensity(self):
        """ Return the light intensity in %.
        Perform the ADC reading and return the light
        intensity in percents (0% - dark, 100% - full light).
        The function is blocking.
        """
        adc_sensor = self.adc.read_u16()
        if (adc_sensor >= self.ADC_MAX):
            self.light = 0
        else:
            r_sensor = adc_sensor * self.R_UP_OHM / (self.ADC_MAX - adc_sensor)
            self.light = 100 + 100 * (r_sensor - self.R_LIGHT_OHM) / (self.R_LIGHT_OHM - self.R_DARK_OHM)
        if self.light < 0:
            self.light = 0
        elif self.light > 100:
            self.light = 100

        if self.light > self.day_night_threshold_pct:
            self.day_night_threshold_pct = self.DAY_LIGHT_PCT - self.DAY_HYSTERESIS_PCT
            _is_day = True
        else:
            self.day_night_threshold_pct = self.DAY_LIGHT_PCT + self.DAY_HYSTERESIS_PCT
            _is_day = False

        if (self.was_day is not _is_day):
            self.was_day = _is_day
            for slot in self.slots:
                slot(_is_day)
        return self.light

    def is_day(self):
        return self.light > self.day_night_threshold_pct

    def register_day_slot(self, slot):
        self.slots.append(slot)
