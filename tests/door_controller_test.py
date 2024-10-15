import pytest

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

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
def door_controller(light_sensor_mock,
                    close_end_switch_mock,
                    open_end_switch_mock,
                    motor_mock):
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        Motor_mock.return_value = motor_mock
        LightSensor_mock.return_value = light_sensor_mock
        EndSwitch_mock.side_effect = { 1 : open_end_switch_mock, 2 : close_end_switch_mock }.get
        return DoorController() 
    
def test_day_on_power_up_drive_motor_open(door_controller,
                                          light_sensor_mock,
                                          motor_mock):
    light_sensor_mock.is_day.return_value = True
    door_controller.start()
    motor_mock.backward.assert_called_once()

def test_night_on_power_up_drive_motor_close(door_controller,
                                             light_sensor_mock,
                                             motor_mock):
    light_sensor_mock.is_day.return_value = False
    door_controller.start()
    motor_mock.forward.assert_called_once()

def test_motor_stops_when_open_end_switch_hit(door_controller,
                                              light_sensor_mock,
                                              close_end_switch_mock,
                                              open_end_switch_mock,
                                              motor_mock):
    light_sensor_mock.is_day.return_value = True
    open_end_switch_mock.is_on.return_value = False
    door_controller.run()
    open_end_switch_mock.is_on.return_value = True
    door_controller.run()
    door_controller.run()
    motor_mock.stop.assert_called_once()
    
