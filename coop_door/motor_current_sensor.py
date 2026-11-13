"""Read motor current through the direction-selectable sense circuit."""
import time
from machine import ADC, Pin  # pylint: disable=import-error


class MotorCurrentSensor:
    """Read signed motor current in amperes.

    The shunt is 0.2 ohms and the sense amplifier gain is 50. The ADC input
    has a 1 ms RC time constant, so the default 5 ms settling delay is five
    time constants.
    """

    ADC_MAX = 65535
    SHUNT_RESISTANCE_OHMS = 0.2
    SENSE_GAIN = 50.0

    def __init__(self, adc_pin_num=28, ref_pin_num=21, vcc_v=3.3,
                 settle_us=5000):
        self.adc = ADC(Pin(adc_pin_num))
        self.ref_pin = Pin(ref_pin_num, Pin.OUT)
        self.vcc_v = vcc_v
        self.settle_us = settle_us
        self.slots = []

    def read(self, current_into_in_plus=True):
        """Return signed current in amperes for the selected direction.

        ``True`` selects GND reference and returns positive current into IN+;
        ``False`` selects VCC reference and returns negative current flowing
        from IN+ to IN-. Current is calculated as V_sense / (gain * R_shunt).
        """
        self.ref_pin.value(0 if current_into_in_plus else 1)

        if self.settle_us:
            # sleep_us is provided by MicroPython; CPython tests patch it.
            time.sleep_us(self.settle_us)  # pylint: disable=no-member

        vout = self.adc.read_u16() * self.vcc_v / self.ADC_MAX
        sense_voltage = vout if current_into_in_plus else vout - self.vcc_v
        current_a = sense_voltage / (
            self.SENSE_GAIN * self.SHUNT_RESISTANCE_OHMS
        )
        for slot in self.slots:
            slot(current_a)
        return current_a

    def register_slot(self, slot):
        """Register a callback for each completed current reading.

        The callback receives the signed current in amperes.
        """
        self.slots.append(slot)
