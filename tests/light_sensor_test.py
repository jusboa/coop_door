import pytest
from unittest.mock import MagicMock
from unittest.mock import patch, call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.light_sensor import LightSensor
import math

R_UP_OHM = 10e3
R_DAY_OHM = 28e3
ADC_MAX = 65535 # 15 bits
R_HYSTERESIS_OHM = 1e3

def ohms_to_adc(ohms):
    return (ADC_MAX * ohms / (ohms + R_UP_OHM))

@pytest.fixture
def adc_mock():
    return MagicMock()

@pytest.fixture
def pin_mock():
    return MagicMock()

@pytest.fixture
def observer_mock():
    return MagicMock()

@pytest.fixture
def light_sensor(adc_mock, pin_mock):
    with (patch('coop_door.coop_door.light_sensor.ADC') as ADC_mock,
          patch('coop_door.coop_door.light_sensor.Pin') as Pin_mock):
        ADC_mock.return_value = adc_mock
        Pin_mock.return_value = pin_mock
        return LightSensor(0, 5)

def test_enable_pin_config():
    with patch('coop_door.coop_door.light_sensor.Pin') as Pin_mock:
        Pin_mock.OUT = 77
        LightSensor(0, 4)
        Pin_mock.assert_called_once_with(4, 77)

def test_adc_channel_config():
    with patch('coop_door.coop_door.light_sensor.ADC') as Adc_mock:
        LightSensor(111, 0)
        Adc_mock.assert_called_once_with(111)

def test_zero_adc_is_full_light(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = 0
    assert light_sensor.read_light_intensity()

def test_full_adc_is_complete_dark(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ADC_MAX
    assert not light_sensor.read_light_intensity()

def test_night(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM + 1)
    assert not light_sensor.read_light_intensity()

def test_day(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM - 1)
    assert light_sensor.read_light_intensity()

def test_from_night_to_day(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(100 * R_DAY_OHM)
    light_sensor.read_light_intensity()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM - R_HYSTERESIS_OHM + 1)
    assert not light_sensor.read_light_intensity()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM - R_HYSTERESIS_OHM - 1)
    assert light_sensor.read_light_intensity()

def test_from_day_to_night(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(0.01 * R_DAY_OHM)
    light_sensor.read_light_intensity()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM + R_HYSTERESIS_OHM - 1)
    assert light_sensor.read_light_intensity()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM + R_HYSTERESIS_OHM + 1)
    assert not light_sensor.read_light_intensity()

def test_call_day_slot_on_change(light_sensor,
                                 adc_mock,
                                 observer_mock):
    light_sensor.register_day_slot(observer_mock)
    adc_mock.read_u16.return_value = ADC_MAX
    light_sensor.read_light_intensity()
    observer_mock.assert_called_with(False)
    adc_mock.read_u16.return_value = 0
    light_sensor.read_light_intensity()
    observer_mock.assert_called_with(True)
    adc_mock.read_u16.return_value = ADC_MAX
    light_sensor.read_light_intensity()
    observer_mock.assert_called_with(False)

def test_status_request(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ADC_MAX
    light_sensor.read_light_intensity()
    assert not light_sensor.is_day()
    adc_mock.read_u16.return_value = 0
    light_sensor.read_light_intensity()
    assert light_sensor.is_day()

def test_unknown_status_on_init(light_sensor):
    assert light_sensor.is_day() is None

def test_sensor_is_enabled_to_be_read(light_sensor,
                                      pin_mock,
                                      adc_mock):
    adc_mock.read_u16.return_value = 0
    light_sensor.read_light_intensity()
    pin_mock.value.assert_has_calls([call(1), call(0)])

del sys.modules['machine']
