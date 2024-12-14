import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.light_sensor import LightSensor
import math

R_UP_OHM = 3.3e3
R_DARK_OHM = 58e3 # when sensor is covered
R_LIGHT_OHM  = 200 # when lighten with a torch
ADC_MAX = 65535 # 15 bits

def light_to_ohms(intensity):
    return (R_LIGHT_OHM + (R_LIGHT_OHM - R_DARK_OHM) / 100 * (intensity - 100))

def light_to_adc(intensity):
    r_sensor_ohm = light_to_ohms(intensity)
    return (ADC_MAX * r_sensor_ohm / (r_sensor_ohm + R_UP_OHM))

@pytest.fixture
def adc_mock():
    return MagicMock()

@pytest.fixture
def observer_mock():
    return MagicMock()

@pytest.fixture
def light_sensor(adc_mock):
    with patch('coop_door.coop_door.light_sensor.ADC') as ADC_mock:
        ADC_mock.return_value = adc_mock
        return LightSensor(0)

def test_zero_adc_is_full_light(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = 0
    assert math.isclose(light_sensor.read_light_intensity(), 100)

def test_full_adc_is_complete_dark(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ADC_MAX
    assert math.isclose(light_sensor.read_light_intensity(), 0, abs_tol=1e-6)

def test_full_dark(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(0)
    assert math.isclose(light_sensor.read_light_intensity(), 0, abs_tol=1e-6)

def test_full_light(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(100)
    assert math.isclose(light_sensor.read_light_intensity(), 100)

def test_half_way(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(50)
    assert math.isclose(light_sensor.read_light_intensity(), 50)

def test_is_not_day(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(0)
    light_sensor.read_light_intensity()
    assert not light_sensor.is_day()

def test_is_day(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(100)
    light_sensor.read_light_intensity()
    assert light_sensor.is_day()

def test_from_dark_to_light(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(0)
    light_sensor.read_light_intensity()
    adc_mock.read_u16.return_value = light_to_adc(59)
    light_sensor.read_light_intensity()
    assert not light_sensor.is_day()
    adc_mock.read_u16.return_value = light_to_adc(61)
    light_sensor.read_light_intensity()
    assert light_sensor.is_day()

def test_from_ligh_to_dark(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = light_to_adc(100)
    light_sensor.read_light_intensity()
    adc_mock.read_u16.return_value = light_to_adc(41)
    light_sensor.read_light_intensity()
    assert light_sensor.is_day()
    adc_mock.read_u16.return_value = light_to_adc(39)
    light_sensor.read_light_intensity()
    assert not light_sensor.is_day()

def test_call_day_slot_on_change(light_sensor,
                                 adc_mock,
                                 observer_mock):
    light_sensor.register_day_slot(observer_mock)
    adc_mock.read_u16.return_value = light_to_adc(0)
    light_sensor.read_light_intensity()
    observer_mock.assert_called_with(False)
    adc_mock.read_u16.return_value = light_to_adc(100)
    light_sensor.read_light_intensity()
    observer_mock.assert_called_with(True)
    adc_mock.read_u16.return_value = light_to_adc(0)
    light_sensor.read_light_intensity()
    observer_mock.assert_called_with(False)
    
