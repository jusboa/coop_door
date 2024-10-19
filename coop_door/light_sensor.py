from machine import ADC

class LightSensor():
    def __init__(self, adc_channel):
        self.slots = []
        self.adc = ADC(adc_channel);
        r_up_ohm = 3.3e3
        r_dark_ohm = 20e6
        r_light_ohm = 190
        adc_max = 65535
        self.ADC_DARK = (adc_max * r_dark_ohm / (r_dark_ohm + r_up_ohm))
        self.ADC_LIGHT = (adc_max * r_light_ohm / (r_light_ohm + r_up_ohm))
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
        self.light = 100 - (self.adc.read_u16() - self.ADC_LIGHT) * 100 / (self.ADC_DARK - self.ADC_LIGHT)
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
