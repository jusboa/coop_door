import pytest

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

from threading import Timer as ThreadTimer

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.door_controller import DoorController

OPEN_END_SWITCH_PIN = 1
CLOSE_END_SWITCH_PIN = 2

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

def create_door_controller(light_sensor_mock,
                           close_end_switch_mock,
                           open_end_switch_mock,
                           motor_mock):
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        Motor_mock.return_value = motor_mock
        LightSensor_mock.return_value = light_sensor_mock
        EndSwitch_mock.side_effect = { OPEN_END_SWITCH_PIN : open_end_switch_mock,
                                       CLOSE_END_SWITCH_PIN : close_end_switch_mock }.get
        controller = DoorController()
        controller.start()
        return controller

@pytest.fixture
def door_controller(light_sensor_mock,
                    close_end_switch_mock,
                    open_end_switch_mock,
                    motor_mock):
    return create_door_controller(light_sensor_mock,
                                  close_end_switch_mock,
                                  open_end_switch_mock,
                                  motor_mock)

def test_hardware_wiring():
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        DoorController()
        assert Motor_mock.called_once_with(2, 3, 6)
        assert EndSwitch_mock.has_calls([call(OPEN_END_SWITCH_PIN),
                                         call(CLOSE_END_SWITCH_PIN)])
        assert LightSensor_mock.called_once_with(2, 1)

def test_refresh_inputs(timer_mock, light_sensor_mock, open_end_switch_mock,
                        close_end_switch_mock):
    with (patch('coop_door.coop_door.door_controller.Timer') as Timer_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock):
        Timer_mock.return_value = timer_mock
        LightSensor_mock.return_value = light_sensor_mock
        EndSwitch_mock.side_effect = { OPEN_END_SWITCH_PIN : open_end_switch_mock,
                                       CLOSE_END_SWITCH_PIN : close_end_switch_mock }.get

        period = 321
        d = DoorController(period)
        d.start()
        assert Timer_mock.called_once()
        assert timer_mock.start.called_once()
        assert Timer_mock.call_args.args[0] == period
        refresh_inputs = Timer_mock.call_args.args[1]
        refresh_inputs()
        refresh_inputs()
        refresh_inputs()
        assert light_sensor_mock.read_light_intensity.call_count == 3

def test_register_light_slot(light_sensor_mock):
    with (patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock):
        LightSensor_mock.return_value = light_sensor_mock
        d = DoorController()
        light_sensor_mock.register_light_slot.assert_called_once_with(d.light_slot)

def test_register_open_end_switch_slot(end_switch_mock):
    with (patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock):
        EndSwitch_mock.return_value = end_switch_mock
        d = DoorController()
        end_switch_mock.register_slot.assert_any_call(d.open_switch_slot)

def test_register_close_end_switch_slot(end_switch_mock):
    with (patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock):
        EndSwitch_mock.return_value = end_switch_mock
        d = DoorController()
        end_switch_mock.register_slot.assert_any_call(d.close_switch_slot)
    
def test_day_on_power_up_open_door(light_sensor_mock,
                                   close_end_switch_mock,
                                   open_end_switch_mock,
                                   motor_mock):
    open_end_switch_mock.is_on.return_value = False
    controller = create_door_controller(light_sensor_mock,
                                        close_end_switch_mock,
                                        open_end_switch_mock,
                                        motor_mock)
    controller.start()
    controller.light_slot(True)
    motor_mock.backward.assert_called_once()

def test_day_comes_door_opened_motor_stays_still(door_controller,
                                                 open_end_switch_mock,
                                                 motor_mock):
    open_end_switch_mock.read.side_effect = lambda:door_controller.open_switch_slot(True)
    door_controller.light_slot(True)
    motor_mock.forward.assert_not_called()
    motor_mock.backward.assert_not_called()

def test_night_on_power_up_close_door(light_sensor_mock,
                                      close_end_switch_mock,
                                      open_end_switch_mock,
                                      motor_mock):
    close_end_switch_mock.is_on.return_value = False
    controller = create_door_controller(light_sensor_mock,
                                        close_end_switch_mock,
                                        open_end_switch_mock,
                                        motor_mock)
    controller.start()
    controller.light_slot(False)
    motor_mock.forward.assert_called_once()

def test_night_comes_door_closed_motor_stays_still(door_controller,
                                                   close_end_switch_mock,
                                                   motor_mock):
    close_end_switch_mock.read.side_effect = lambda:door_controller.close_switch_slot(True)
    door_controller.light_slot(False)
    motor_mock.forward.assert_not_called()
    motor_mock.backward.assert_not_called()

def test_motor_stops_when_open_end_switch_hit(door_controller,
                                              open_end_switch_mock,
                                              motor_mock):
    open_end_switch_mock.read.side_effect = lambda:door_controller.open_switch_slot(False)
    door_controller.light_slot(True)
    door_controller.open_switch_slot(True)
    motor_mock.stop.assert_called_once()

def test_motor_stops_when_close_end_switch_hit(door_controller,
                                               close_end_switch_mock,
                                               motor_mock):
    close_end_switch_mock.read.side_effect = lambda:door_controller.close_switch_slot(False)
    door_controller.light_slot(False)
    door_controller.close_switch_slot(True)
    motor_mock.stop.assert_called_once()

def test_night_comes_close_door(door_controller,
                                close_end_switch_mock,
                                motor_mock):
    door_controller.light_slot(True)
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    motor_mock.forward.assert_called_once()
    motor_mock.backward.assert_not_called()

def test_day_comes_open_door(door_controller,
                             open_end_switch_mock,
                             motor_mock):
    door_controller.light_slot(False)
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(True)
    open_end_switch_mock.is_on.assert_called_once()

def test_day_comes_while_closing_open_door(door_controller,
                                           close_end_switch_mock,
                                           open_end_switch_mock,
                                           motor_mock):
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    motor_mock.forward.assert_called_once()
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(True)
    motor_mock.backward.assert_called_once()

def test_night_comes_while_opening_close_door(door_controller,
                                              close_end_switch_mock,
                                              open_end_switch_mock,
                                              motor_mock):
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(True)
    motor_mock.backward.assert_called_once()
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    motor_mock.forward.assert_called_once()

# def test_reverse_motor_on_stuck_close_end(door_controller,
#                                           motor_mock):
#     door_controller.open_switch_slot(False)
#     door_controller.close_switch_slot(True)
#     door_controller.light_slot(True)
#     motor_mock.backward.assert_called_once()
#     # After 1s when close end switch does not open
#     # reverse the motor direction.
#     for i in range(round(1e3 / WAKEUP_PERIOD_MS)):
#         WAKEUP_CALLBACK()
#     motor_mock.forward.assert_called_once()

del sys.modules['machine']
