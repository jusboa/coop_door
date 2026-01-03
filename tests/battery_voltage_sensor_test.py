import pytest
from unittest.mock import MagicMock
from unittest.mock import patch, call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.battery_voltage_sensor import BatteryVoltageSensor
import math

R_UP_OHM = 15e3
R_DOWN_OHM = 5e3
ADC_MAX = 65535 # 15 bits
VCC_V = 3.2
V_DIFF = 1e-6

def v_to_adc(v):
    return (((v * R_DOWN_OHM * ADC_MAX) / (R_DOWN_OHM + R_UP_OHM)) / VCC_V)

def is_close_to(v1, v2):
    return (abs(v1 - v2) < V_DIFF)

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
def sensor(adc_mock,
           timer_mock):
    with (patch('coop_door.coop_door.battery_voltage_sensor.ADC') as ADC_mock,
          patch('coop_door.coop_door.battery_voltage_sensor.Timer') as Timer_mock):
        ADC_mock.return_value = adc_mock
        Timer_mock.return_value = timer_mock
        timer_mock.active.return_value = False
        return BatteryVoltageSensor(0)

def test_adc_channel_config(pin_mock):
    with (patch('coop_door.coop_door.battery_voltage_sensor.ADC') as ADC_mock,
          patch('coop_door.coop_door.battery_voltage_sensor.Pin') as Pin_mock):
        Pin_mock.return_value = pin_mock
        BatteryVoltageSensor(777)
        Pin_mock.assert_called_once_with(777)
        ADC_mock.assert_called_once_with(pin_mock)

def test_gives_none_during_init_delay(sensor,
                                      adc_mock,
                                      timer_mock):
    adc_mock.read_u16.return_value = 333
    timer_mock.active.return_value = True
    assert sensor.read() is None

def test_timer_starts_on_init(sensor,
                              timer_mock):
    timer_mock.start.assert_called_once()

def test_init_delay_value():
    with patch('coop_door.coop_door.battery_voltage_sensor.Timer') as Timer_mock:
        BatteryVoltageSensor(0)
        assert Timer_mock.call_args.args[0] == 1 # ms

def test_sensor_reads_after_init_delay(sensor,
                                       timer_mock,
                                       adc_mock):
    adc_mock.read_u16.return_value = 333
    timer_mock.active.return_value = True
    assert sensor.read() is None
    timer_mock.active.return_value = False
    assert sensor.read() is not None

def test_call_slot_on_complete_reading(sensor,
                                       adc_mock,
                                       observer_mock,
                                       timer_mock):
    sensor.register_slot(observer_mock)
    adc_mock.read_u16.return_value = 12345
    timer_mock.active.return_value = True
    sensor.read()
    observer_mock.assert_not_called()
    timer_mock.active.return_value = False
    sensor.read()
    observer_mock.assert_called_once()

def test_zero_adc_is_zero_voltage(sensor,
                                  adc_mock):
    adc_mock.read_u16.return_value = 0
    assert sensor.read() == 0

def test_selected_voltages(sensor,
                           adc_mock):
    voltages = [2.2, 6.3, 0.023, 10.256, 5.552]
    for v in voltages:
        adc_mock.read_u16.return_value = v_to_adc(v)
        assert is_close_to(sensor.read(), v)

def test_report_voltage(sensor,
                        adc_mock,
                        observer_mock):
    sensor.register_slot(observer_mock)
    adc_mock.read_u16.return_value = v_to_adc(1.2)
    sensor.read()
    assert is_close_to(observer_mock.call_args.args[0], 1.2)
    adc_mock.read_u16.return_value = 0
    sensor.read()
    observer_mock.assert_called_with(0)
    adc_mock.read_u16.return_value = v_to_adc(6.6)
    sensor.read()
    assert is_close_to(observer_mock.call_args.args[0], 6.6)
    # Slot is called even when voltages does not change.
    observer_mock.reset_mock()
    sensor.read()
    observer_mock.assert_called_once()
    assert is_close_to(observer_mock.call_args.args[0], 6.6)

del sys.modules['machine']
