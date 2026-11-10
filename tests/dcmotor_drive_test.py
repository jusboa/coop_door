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
    pin_mock[2].value.reset_mock()
    motor.go(+1)
    pin_mock[2].value.assert_called_once_with(True)
    pin_mock[2].value.reset_mock()
    motor.stop()
    pin_mock[2].value.assert_called_once_with(False)
    pin_mock[2].value.reset_mock()
    motor.go(-1)
    pin_mock[2].value.assert_called_once_with(True)
    pin_mock[2].value.reset_mock()
    motor.stop()
    pin_mock[2].value.assert_called_once_with(False)

def test_pwm_initialized_once_at_startup(motor, pwm_mock, freq_hz):
    for pwm in pwm_mock:
        pwm.init.assert_called_once_with(freq=freq_hz, duty_u16=0)

def test_drive_forward(motor, pwm_mock):
    motor.go(+1)
    pwm_mock[0].duty_u16.assert_called_once_with(0)
    pwm_mock[1].duty_u16.assert_called_once_with(Motor.DUTY_MAX)
    for pwm in pwm_mock:
        pwm.init.assert_called_once_with(freq=Motor.FREQ_HZ, duty_u16=0)

def test_drive_backward(motor, pwm_mock):
    motor.go(-1)
    pwm_mock[0].duty_u16.assert_called_once_with(Motor.DUTY_MAX)
    pwm_mock[1].duty_u16.assert_called_once_with(0)
    for pwm in pwm_mock:
        pwm.init.assert_called_once_with(freq=Motor.FREQ_HZ, duty_u16=0)

def test_stop_motor(motor, pwm_mock):
    motor.go(+1)
    pwm_mock[0].duty_u16.reset_mock()
    pwm_mock[1].duty_u16.reset_mock()
    motor.stop()
    pwm_mock[0].duty_u16.assert_called_once_with(0)
    pwm_mock[1].duty_u16.assert_called_once_with(0)
    motor.go(-1)
    pwm_mock[0].duty_u16.reset_mock()
    pwm_mock[1].duty_u16.reset_mock()
    motor.stop()
    pwm_mock[0].duty_u16.assert_called_once_with(0)
    pwm_mock[1].duty_u16.assert_called_once_with(0)

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

def test_pwm(motor, pwm_mock, voltage_callback):
    voltages = [6, 7, 8, 9, 10, 11, 11.99]
    for v in voltages:
        duty = voltage_to_duty(v)
        voltage_callback.return_value = v
        pwm_mock[0].duty_u16.reset_mock()
        pwm_mock[1].duty_u16.reset_mock()
        motor.go(+1)
        pwm_mock[0].duty_u16.assert_called_once_with(Motor.DUTY_MAX - duty)
        pwm_mock[1].duty_u16.assert_called_once_with(Motor.DUTY_MAX)
        pwm_mock[0].duty_u16.reset_mock()
        pwm_mock[1].duty_u16.reset_mock()
        motor.go(-1)
        pwm_mock[0].duty_u16.assert_called_once_with(Motor.DUTY_MAX)
        pwm_mock[1].duty_u16.assert_called_once_with(Motor.DUTY_MAX - duty)
        for pwm in pwm_mock:
            pwm.init.assert_called_once_with(freq=Motor.FREQ_HZ, duty_u16=0)

def test_drive_skips_when_direction_and_duty_unchanged(motor, pwm_mock):
    motor.go(+1)
    for pwm in pwm_mock:
        pwm.duty_u16.reset_mock()
    motor.go(+1)
    for pwm in pwm_mock:
        pwm.duty_u16.assert_not_called()
    for pwm in pwm_mock:
        pwm.init.assert_called_once_with(freq=Motor.FREQ_HZ, duty_u16=0)

def test_drive_skips_when_stopped_twice(motor, pwm_mock):
    motor.stop()
    for pwm in pwm_mock:
        pwm.duty_u16.reset_mock()
    motor.stop()
    for pwm in pwm_mock:
        pwm.duty_u16.assert_not_called()

def test_pwm_max(motor, pwm_mock, voltage_callback):
    voltage_callback.return_value = 5.9
    motor.go(+1)
    pwm_mock[0].duty_u16.assert_called_once_with(
        Motor.DUTY_MAX - motor.duty)
    pwm_mock[1].duty_u16.assert_called_once_with(Motor.DUTY_MAX)

def test_voltage_low(motor, pwm_mock, voltage_callback):
    voltage_callback.return_value = 3.9
    motor.go(+1)
    assert motor.direction() == 0
    assert not motor.is_running()
    for pwm in pwm_mock:
        pwm.init.assert_called_once_with(freq=Motor.FREQ_HZ, duty_u16=0)
        pwm.duty_u16.assert_not_called()

def test_voltage_high(motor, pwm_mock, voltage_callback):
    voltage_callback.return_value = 12.1
    motor.go(+1)
    assert motor.direction() == 0
    assert not motor.is_running()
    for pwm in pwm_mock:
        pwm.init.assert_called_once_with(freq=Motor.FREQ_HZ, duty_u16=0)
        pwm.duty_u16.assert_not_called()

del sys.modules['machine']
