""" Driver of a DC motor. """
import logging
from machine import Pin, PWM # pylint: disable=import-error

logger = logging.getLogger(__name__)

class Motor():
    """ Drive motor back and forth or stop it.
    Control the motor voltage via a duty cycle. """

    VOLTAGE_NOMINAL_V = 6
    VOLTAGE_MIN_V = 4
    VOLTAGE_MAX_V = 12
    FREQ_HZ = 10000
    DUTY_MAX = 65535
    def __init__(self,
                 gpio0, gpio1,
                 gpio_en,
                 voltage_callback):
        self.drive_value = [False, False]
        self._direction = 0
        pin0 = Pin(gpio0, Pin.OUT)
        pin1 = Pin(gpio1, Pin.OUT)
        self.enable_pin = Pin(gpio_en, Pin.OUT)
        self.drive = [PWM(pin0), PWM(pin1)]
        self.voltage_callback = voltage_callback
        self.duty = 0

    def _drive(self):
        self.enable_pin.value(self._direction != 0)
        if self._direction > 0:
            self.drive[0].init(freq=Motor.FREQ_HZ,
                               duty_u16=self.duty)
            self.drive[1].init(freq=Motor.FREQ_HZ, duty_u16=0)
        elif self._direction < 0:
            self.drive[0].init(freq=Motor.FREQ_HZ, duty_u16=0)
            self.drive[1].init(freq=Motor.FREQ_HZ,
                               duty_u16=self.duty)
        else:
            self.drive[0].init(freq=Motor.FREQ_HZ, duty_u16=0)
            self.drive[1].init(freq=Motor.FREQ_HZ, duty_u16=0)

    def _is_voltage_ok(self, v):
        return v is not None and \
            Motor.VOLTAGE_MIN_V <= v <= Motor.VOLTAGE_MAX_V

    def _v_to_duty(self, volts):
        duty = round(Motor.DUTY_MAX * Motor.VOLTAGE_NOMINAL_V / volts)
        duty = min(duty, Motor.DUTY_MAX)
        return duty

    def go(self, direction):
        """ Run the motor in a given direction (+/-1) """
        self._direction = direction
        v = self.voltage_callback()
        logger.debug('v = %f V', v)
        if not self._is_voltage_ok(v):
            self.stop()
            return
        self.duty = self._v_to_duty(v)
        logger.debug('duty = %d', self.duty)
        self._drive()

    def stop(self):
        """ Stop the motor. """
        self._direction = 0
        self._drive()

    def direction(self):
        """ Return the motor direction (+/-1). """
        return self._direction

    def is_running(self):
        """ Return True if motor is running. """
        return self._direction != 0
