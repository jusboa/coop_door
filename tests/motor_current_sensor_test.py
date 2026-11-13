from unittest.mock import MagicMock, patch

import pytest

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.motor_current_sensor import MotorCurrentSensor


@pytest.fixture
def sensor():
    with (patch('coop_door.coop_door.motor_current_sensor.ADC') as adc_class,
          patch('coop_door.coop_door.motor_current_sensor.Pin') as pin_class):
        adc = MagicMock()
        pin = MagicMock()
        adc_class.return_value = adc
        pin_class.return_value = pin
        current_sensor = MotorCurrentSensor(settle_us=0)
        yield current_sensor, adc, pin


def test_positive_current_conversion_and_slot(sensor):
    current_sensor, adc, pin = sensor
    callback = MagicMock()
    current_sensor.register_slot(callback)
    # 1.0 V output gives 0.1 A with gain=50 and 0.2 ohm shunt.
    adc.read_u16.return_value = round(1.0 * current_sensor.ADC_MAX / 3.3)

    current_a = current_sensor.read()

    assert abs(current_a - 0.1) < 0.0001
    pin.value.assert_called_once_with(0)
    callback.assert_called_once_with(current_a)


def test_negative_current_conversion(sensor):
    current_sensor, adc, pin = sensor
    # 2.3 V output relative to 3.3 V supply is 1.0 V from VCC.
    adc.read_u16.return_value = round(2.3 * current_sensor.ADC_MAX / 3.3)

    current_a = current_sensor.read(current_into_in_plus=False)

    assert abs(current_a + 0.1) < 0.0001
    pin.value.assert_called_once_with(1)


def test_callbacks_called_for_each_reading(sensor):
    current_sensor, adc, _ = sensor
    callback = MagicMock()
    current_sensor.register_slot(callback)
    adc.read_u16.return_value = 0

    current_sensor.read()
    current_sensor.read()

    assert callback.call_count == 2


def test_settling_delay(sensor):
    current_sensor, adc, _ = sensor
    current_sensor.settle_us = 125
    adc.read_u16.return_value = 0
    with patch('time.sleep_us', create=True) as sleep_us:
        current_sensor.read()
    sleep_us.assert_called_once_with(125)


del sys.modules['machine']
