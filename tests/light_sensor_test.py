import pytest
from unittest.mock import MagicMock
from unittest.mock import patch, call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.light_sensor import LightSensor

R_UP_OHM = 10e3
R_DAY_OHM = 70e3
ADC_MAX = 65535 # 15 bits
R_HYSTERESIS_OHM = 4e3

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
def timer_mock():
    return MagicMock()

@pytest.fixture
def light_sensor(adc_mock, pin_mock, timer_mock):
    with (patch('coop_door.coop_door.light_sensor.ADC') as ADC_mock,
          patch('coop_door.coop_door.light_sensor.Pin') as Pin_mock,
          patch('coop_door.coop_door.light_sensor.Timer') as Timer_mock):
        ADC_mock.return_value = adc_mock
        Pin_mock.return_value = pin_mock
        Timer_mock.return_value = timer_mock
        timer_mock.active.return_value = False
        return LightSensor(0, 5)

def test_enable_pin_config():
    with patch('coop_door.coop_door.light_sensor.Pin') as Pin_mock:
        Pin_mock.OUT = 77
        LightSensor(0, 4)
        Pin_mock.assert_any_call(4, 77)

def test_adc_channel_config(pin_mock):
    with (patch('coop_door.coop_door.light_sensor.ADC') as Adc_mock,
          patch('coop_door.coop_door.light_sensor.Pin') as Pin_mock):
        Pin_mock.return_value = pin_mock
        LightSensor(111, 0)
        Pin_mock.assert_any_call(111)
        Adc_mock.assert_called_once_with(pin_mock)

def test_sensor_is_enabled_on_wakeup(light_sensor,
                                     pin_mock):
    light_sensor.wakeup()
    pin_mock.value.assert_called_once_with(1)

def test_sensor_is_disabled_on_sleep(light_sensor,
                                     pin_mock):
    light_sensor.sleep()
    pin_mock.value.assert_called_once_with(0)

def test_sleeping_sensor_gives_none(light_sensor,
                                    adc_mock,
                                    timer_mock):
    adc_mock.read_u16.return_value = 333
    timer_mock.active.return_value = True
    light_sensor.read()
    assert light_sensor.is_day() is None

def test_wakeup_starts_timer(light_sensor,
                             timer_mock):
    light_sensor.wakeup()
    timer_mock.start.assert_called_once()

def test_sensor_reads_after_wakeup_delay(light_sensor,
                                         timer_mock,
                                         adc_mock):
    adc_mock.read_u16.return_value = 333
    timer_mock.active.return_value = True
    light_sensor.wakeup()
    light_sensor.read()
    assert light_sensor.is_day() is None
    timer_mock.active.return_value = False
    light_sensor.read()
    assert light_sensor.is_day() is not None

def test_wakeup_delay_value():
    with patch('coop_door.coop_door.light_sensor.Timer') as Timer_mock:
        LightSensor(0, 0)
        assert Timer_mock.call_args.args[0] == 250 # ms

def test_call_light_slot_on_complete_reading(light_sensor,
                                             adc_mock,
                                             observer_mock,
                                             timer_mock):
    light_sensor.register_light_slot(observer_mock)
    adc_mock.read_u16.return_value = 12345
    timer_mock.active.return_value = True
    light_sensor.wakeup()
    light_sensor.read()
    observer_mock.assert_not_called()
    timer_mock.active.return_value = False
    light_sensor.read()
    observer_mock.assert_called_once()

def test_zero_adc_is_full_light(light_sensor,
                                adc_mock):
    adc_mock.read_u16.return_value = 0
    light_sensor.read()
    assert light_sensor.is_day()

def test_full_adc_is_complete_dark(light_sensor,
                                   adc_mock):
    adc_mock.read_u16.return_value = ADC_MAX
    light_sensor.read()
    assert not light_sensor.is_day()

def test_night(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM + 1)
    light_sensor.read()
    assert not light_sensor.is_day()

def test_day(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM - 1)
    light_sensor.read()
    assert light_sensor.is_day()

def test_from_night_to_day(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(100 * R_DAY_OHM)
    light_sensor.read()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM - R_HYSTERESIS_OHM + 1)
    light_sensor.read()
    assert not light_sensor.is_day()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM - R_HYSTERESIS_OHM - 1)
    light_sensor.read()
    assert light_sensor.is_day()

def test_from_day_to_night(light_sensor, adc_mock):
    adc_mock.read_u16.return_value = ohms_to_adc(0.01 * R_DAY_OHM)
    light_sensor.read()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM + R_HYSTERESIS_OHM - 1)
    light_sensor.read()
    assert light_sensor.is_day()
    adc_mock.read_u16.return_value = ohms_to_adc(R_DAY_OHM + R_HYSTERESIS_OHM + 1)
    light_sensor.read()
    assert not light_sensor.is_day()

def test_report_day(light_sensor,
                    adc_mock,
                    observer_mock):
    light_sensor.register_light_slot(observer_mock)
    adc_mock.read_u16.return_value = ADC_MAX
    light_sensor.read()
    observer_mock.assert_called_with(False)
    adc_mock.read_u16.return_value = 0
    light_sensor.read()
    observer_mock.assert_called_with(True)
    adc_mock.read_u16.return_value = ADC_MAX
    light_sensor.read()
    observer_mock.assert_called_with(False)
    # Called even when light has not changed
    light_sensor.read()
    observer_mock.assert_called_with(False)

del sys.modules['machine']
