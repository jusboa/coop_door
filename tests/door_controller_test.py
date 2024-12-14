import pytest

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import time

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.door_controller import DoorController

@pytest.fixture
def end_switch_mock():
    return MagicMock()

@pytest.fixture
def motor_mock():
    return MagicMock()

@pytest.fixture
def light_sensor_mock():
    return MagicMock()

@pytest.fixture
def open_end_switch_mock():
    return MagicMock()

@pytest.fixture
def close_end_switch_mock():
    return MagicMock()

@pytest.fixture
def timer_mock():
    return MagicMock()

@pytest.fixture
def timer_slot():
    return lambda:'door_controller_test_timer_slot'

@pytest.fixture
def door_controller(light_sensor_mock,
                    close_end_switch_mock,
                    open_end_switch_mock,
                    motor_mock,
                    timer_mock):
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
          patch('coop_door.coop_door.door_controller.Timer') as Timer_mock):
        Motor_mock.return_value = motor_mock
        LightSensor_mock.return_value = light_sensor_mock
        EndSwitch_mock.side_effect = { 4 : open_end_switch_mock, 5 : close_end_switch_mock }.get
        Timer_mock.return_value = timer_mock
        return DoorController()

def test_hardware_wiring():
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        DoorController()
        assert Motor_mock.called_once_with(2, 3)
        assert EndSwitch_mock.has_calls([call(4), call(5)])
        assert LightSensor_mock.called_once_with(2)

def test_light_sensor_timer_init(timer_mock, timer_slot, light_sensor_mock):
    with (patch('coop_door.coop_door.door_controller.Timer') as Timer_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock):
        Timer_mock.return_value = timer_mock
        LightSensor_mock.return_value = light_sensor_mock
        period = 321
        DoorController(period)
        assert Timer_mock.called_once()
        assert Timer_mock.call_args.args[0] == period
        read_light = Timer_mock.call_args.args[1]
        read_light()
        read_light()
        read_light()
        assert light_sensor_mock.read_light_intensity.call_count == 3
        assert timer_mock.start.called_once()
    
def test_register_day_slot(light_sensor_mock):
    with (patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock):
        LightSensor_mock.return_value = light_sensor_mock
        d = DoorController()
        light_sensor_mock.register_day_slot.assert_called_once_with(d.day_slot)

def test_register_open_end_switch_slot(end_switch_mock):
    with (patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        EndSwitch_mock.return_value = end_switch_mock
        d = DoorController()
        end_switch_mock.register_slot.assert_any_call(d.open_switch_slot)

def test_register_close_end_switch_slot(end_switch_mock):
    with (patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        EndSwitch_mock.return_value = end_switch_mock
        d = DoorController()
        end_switch_mock.register_slot.assert_any_call(d.close_switch_slot)
    
def test_day_on_power_up_drive_motor_open(door_controller,
                                          motor_mock):
    door_controller.day_slot(True)
    motor_mock.backward.assert_called_once()

def test_night_on_power_up_drive_motor_close(door_controller,
                                             motor_mock):
    door_controller.day_slot(False)
    motor_mock.forward.assert_called_once()

def test_motor_stops_when_open_end_switch_hit(door_controller,
                                              motor_mock):
    door_controller.open_switch_slot(False)
    door_controller.day_slot(True)
    door_controller.open_switch_slot(True)
    motor_mock.stop.assert_called_once()

def test_motor_stops_when_close_end_switch_hit(door_controller,
                                               motor_mock):
    door_controller.close_switch_slot(False)
    door_controller.day_slot(False)
    door_controller.close_switch_slot(True)
    motor_mock.stop.assert_called_once()

def test_door_opened_drive_close_in_night(door_controller,
                                          motor_mock):
    door_controller.day_slot(True)
    door_controller.open_switch_slot(True)
    door_controller.day_slot(False)
    motor_mock.forward.assert_called_once()

def test_door_closed_drive_open_in_day(door_controller,
                                       motor_mock):
    door_controller.day_slot(False)
    door_controller.close_switch_slot(True)
    door_controller.day_slot(True)
    motor_mock.backward.assert_called_once()
