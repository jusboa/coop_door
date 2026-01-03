import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.dcmotor_drive import Motor

@pytest.fixture
def pin_mock():
    return (MagicMock(), MagicMock(), MagicMock())

@pytest.fixture
def pwm_mock():
    return (MagicMock(), MagicMock())

@pytest.fixture
def voltage_callback():
    return MagicMock()

@pytest.fixture
def freq_hz():
    return 10000

def voltage_to_duty(v):
    return round(65535 * 6 / v)

@pytest.fixture
def motor(pin_mock,
          pwm_mock,
          voltage_callback):
    with (patch('coop_door.coop_door.dcmotor_drive.Pin') as Pin_mock,
          patch('coop_door.coop_door.dcmotor_drive.PWM') as PWM_mock):
        Pin_mock.side_effect = [pin_mock[0], pin_mock[1], pin_mock[2]]
        PWM_mock.side_effect = [pwm_mock[0], pwm_mock[1]]
        voltage_callback.return_value = 6
        return Motor(0, 1, 2, voltage_callback)

def test_pin_config(pin_mock, voltage_callback):
    with (patch('coop_door.coop_door.dcmotor_drive.Pin') as Pin_mock,
          patch('coop_door.coop_door.dcmotor_drive.PWM') as PWM_mock):
        Pin_mock.OUT = 33
        Pin_mock.side_effect = [pin_mock[0], pin_mock[1], pin_mock[2]]
        Motor(0, 1, 2, voltage_callback)
        Pin_mock.assert_has_calls([call(0, 33), call(1, 33), call(2, 33)], any_order=True)
        PWM_mock.assert_has_calls([call(pin_mock[0]), call(pin_mock[1])], any_order=True)
        

def test_enable_driver_while_driving_motor(motor, pin_mock):
    motor.go(+1)
    pin_mock[2].value.assert_called_once_with(True)
    pin_mock[2].reset_mock()
    motor.stop()
    pin_mock[2].value.assert_called_once_with(False)
    pin_mock[2].reset_mock()
    motor.go(-1)
    pin_mock[2].value.assert_called_once_with(True)
    pin_mock[2].reset_mock()
    motor.stop()
    pin_mock[2].value.assert_called_once_with(False)

def test_drive_forward(motor, pwm_mock, freq_hz):
    motor.go(+1)
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=65535)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)

def test_drive_backward(motor, pwm_mock, freq_hz):
    motor.go(-1)
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=65535)

def test_stop_motor(motor, pwm_mock, freq_hz):
    motor.go(+1)
    pwm_mock[0].init.reset_mock()
    pwm_mock[1].init.reset_mock()
    motor.stop()
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
    motor.go(-1)
    pwm_mock[0].init.reset_mock()
    pwm_mock[1].init.reset_mock()
    motor.stop()
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)

def test_get_direction(motor):
    assert motor.direction() == 0
    motor.go(-1)
    assert motor.direction() == -1
    motor.go(+1)
    assert motor.direction() == 1
    motor.stop()
    assert motor.direction() == 0

def test_is_running(motor):
    assert not motor.is_running()
    motor.go(-1)
    assert motor.is_running()
    motor.stop()
    assert not motor.is_running()
    motor.go(+1)
    assert motor.is_running()

def test_go_zero_stops_motor(motor):
    assert not motor.is_running()
    motor.go(-1)
    assert motor.is_running()
    motor.go(0)
    assert not motor.is_running()

def test_pwm(motor,
             pwm_mock,
             voltage_callback,
             freq_hz):
    voltages = [6, 7, 8, 9, 10, 11, 11.99]
    for v in voltages:
        duty = voltage_to_duty(v)
        voltage_callback.return_value = v
        pwm_mock[0].init.reset_mock()
        pwm_mock[1].init.reset_mock()
        motor.go(+1)
        pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=duty)
        pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
        pwm_mock[0].init.reset_mock()
        pwm_mock[1].init.reset_mock()
        motor.go(-1)
        pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
        pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=duty)

def test_pwm_max(motor,
                 pwm_mock,
                 voltage_callback,
                 freq_hz):
    voltage_callback.return_value = 5.9
    motor.go(+1)
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=65535)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)

def test_voltage_low(motor,
                     pwm_mock,
                     voltage_callback,
                     freq_hz):
    voltage_callback.return_value = 3.9
    motor.go(+1)
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)

def test_voltage_high(motor,
                      pwm_mock,
                      voltage_callback,
                      freq_hz):
    voltage_callback.return_value = 12.1
    motor.go(+1)
    pwm_mock[0].init.assert_called_once_with(freq=freq_hz, duty_u16=0)
    pwm_mock[1].init.assert_called_once_with(freq=freq_hz, duty_u16=0)

del sys.modules['machine']
