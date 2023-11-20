from machine import ADC

class LightSensor():
    def __init__(self, adc_channel):
        self.adc = ADC(adc_channel);
        r_up_ohm = 3.3e3
        r_dark_ohm = 20e6
        r_light_ohm = 190
        adc_max = 65535
        self.ADC_DARK = (adc_max * r_dark_ohm / (r_dark_ohm + r_up_ohm))
        self.ADC_LIGHT = (adc_max * r_light_ohm / (r_light_ohm + r_up_ohm))

    def read_light_intensity(self):
        """ Return the light intensity in %.
        Perform the ADC reading and return the light
        intensity in percents (0% - dark, 100% - full light).
        The function is blocking.
        """
        light = 100 + (self.adc.read_u16() - self.ADC_LIGHT) * 100 / (self.ADC_LIGHT - self.ADC_DARK)
        if light < 0:
            light = 0
        elif light > 100:
            light = 100
        return light
