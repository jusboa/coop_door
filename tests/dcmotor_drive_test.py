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
def motor(pin_mock):
    with patch('coop_door.coop_door.dcmotor_drive.Pin') as Pin_mock:
        Pin_mock.side_effect = [pin_mock[0], pin_mock[1], pin_mock[2]]
        return Motor(0, 1, 2)

def test_pin_config():
    with patch('coop_door.coop_door.dcmotor_drive.Pin') as Pin_mock:
        Pin_mock.OUT = 33
        Motor(0, 1, 2)
        Pin_mock.assert_has_calls([call(0, 33), call(1, 33), call(2, 33)])

def test_enable_driver_while_driving_motor(motor, pin_mock):
    motor.go(+1)
    pin_mock[2].value.assert_called_once_with(1)
    pin_mock[2].reset_mock()
    motor.stop()
    pin_mock[2].value.assert_called_once_with(0)
    pin_mock[2].reset_mock()
    motor.go(-1)
    pin_mock[2].value.assert_called_once_with(1)
    pin_mock[2].reset_mock()
    motor.stop()
    pin_mock[2].value.assert_called_once_with(0)

def test_drive_forward(motor, pin_mock):
    motor.go(+1)
    pin_mock[0].value.assert_called_once_with(1)
    pin_mock[1].value.assert_called_once_with(0)

def test_drive_backward(motor, pin_mock):
    motor.go(-1)
    pin_mock[0].value.assert_called_once_with(0)
    pin_mock[1].value.assert_called_once_with(1)

def test_stop_motor(motor, pin_mock):
    motor.go(+1)
    pin_mock[0].value.reset_mock()
    pin_mock[1].value.reset_mock()
    motor.stop()
    pin_mock[0].value.assert_called_once_with(0)
    pin_mock[1].value.assert_called_once_with(0)
    motor.go(-1)
    pin_mock[0].value.reset_mock()
    pin_mock[1].value.reset_mock()
    motor.stop()
    pin_mock[0].value.assert_called_once_with(0)
    pin_mock[1].value.assert_called_once_with(0)

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

del sys.modules['machine']
