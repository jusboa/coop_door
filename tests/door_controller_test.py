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

@pytest.fixture()
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
def timer_mock_factory():
    def make_timer():
        return MagicMock()
    return make_timer

@pytest.fixture
def timer_mock():
    return MagicMock()

def fake_time_elapsed(timers, elapsed_time_ms):
    for timer, timeout_ms, callback in timers:
        if timeout_ms <= elapsed_time_ms\
           and timer.start.call_count > timer.stop.call_count:
            callback()

@pytest.fixture
def timers():
    return []

@pytest.fixture
def sleep_pin_mock():
    return MagicMock()
    
@pytest.fixture
def door_controller_factory(light_sensor_mock,
                            close_end_switch_mock,
                            open_end_switch_mock,
                            motor_mock,
                            timers,
                            timer_mock_factory,
                            sleep_pin_mock):
    def make_door_controller():
        with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
              patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
              patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
              patch('coop_door.coop_door.state_machine.Timer') as StateTimer_mock,
              patch('coop_door.coop_door.door_controller.Pin') as Pin_mock):
            Motor_mock.return_value = motor_mock
            LightSensor_mock.return_value = light_sensor_mock
            Pin_mock.return_value = sleep_pin_mock
            EndSwitch_mock.side_effect = { OPEN_END_SWITCH_PIN : open_end_switch_mock,
                                           CLOSE_END_SWITCH_PIN : close_end_switch_mock }.get
            return_value = []
            def side_effect(*args, **kwargs):
                return_value.append(timer_mock_factory())
                return return_value[-1]
            StateTimer_mock.side_effect = side_effect
            controller = DoorController()
            timers.extend([
                ( return_value[i],
                  StateTimer_mock.call_args_list[i].args[0],
                  StateTimer_mock.call_args_list[i].args[1] ) \
                for i in range(len(StateTimer_mock.call_args_list))])
            return controller
    return make_door_controller

@pytest.fixture
def door_controller(door_controller_factory):
    c = door_controller_factory()
    c.start()
    return c

@pytest.fixture
def detach_from_end_timeout_ms():
    return 2000

def test_hardware_wiring():
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
          patch('coop_door.coop_door.door_controller.Pin') as Pin_mock):
        Pin_mock.OUT = 33
        DoorController()
        Motor_mock.assert_called_once_with(14, 15, 6)
        EndSwitch_mock.has_calls([call(OPEN_END_SWITCH_PIN),
                                  call(CLOSE_END_SWITCH_PIN)])
        LightSensor_mock.assert_called_once_with(2, 0)
        Pin_mock.assert_called_once_with(22, 33)

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
        Timer_mock.called_once()
        timer_mock.start.assert_called_once()
        assert Timer_mock.call_args.args[0] == period
        refresh_inputs = Timer_mock.call_args.args[1]
        refresh_inputs()
        refresh_inputs()
        refresh_inputs()
        assert light_sensor_mock.read_light_intensity.call_count == 3

def test_register_light_slot(door_controller, light_sensor_mock):
    light_sensor_mock.register_light_slot.assert_called_once_with(door_controller.light_slot)

def test_register_open_end_switch_slot(door_controller, open_end_switch_mock):
    open_end_switch_mock.register_slot.assert_called_once_with(door_controller.open_switch_slot)

def test_register_close_end_switch_slot(door_controller, close_end_switch_mock):
    close_end_switch_mock.register_slot.assert_called_once_with(door_controller.close_switch_slot)
    
def test_day_on_power_up_open_door(door_controller_factory,
                                   open_end_switch_mock,
                                   motor_mock):
    open_end_switch_mock.is_on.return_value = False
    controller = door_controller_factory()
    controller.start()
    controller.light_slot(True)
    controller.do_all()
    motor_mock.go.assert_called_once_with(-1)

def test_day_comes_door_opened_motor_stays_still(door_controller,
                                                 open_end_switch_mock,
                                                 motor_mock):
    open_end_switch_mock.read.side_effect = lambda:door_controller.open_switch_slot(True)
    door_controller.light_slot(True)
    door_controller.do_all()
    motor_mock.go.assert_not_called()

def test_night_on_power_up_close_door(door_controller_factory,
                                      close_end_switch_mock,
                                      motor_mock):
    close_end_switch_mock.is_on.return_value = False
    controller = door_controller_factory()
    controller.start()
    controller.light_slot(False)
    controller.do_all()
    motor_mock.go.assert_called_once_with(+1)

def test_night_comes_door_closed_motor_stays_still(door_controller,
                                                   close_end_switch_mock,
                                                   motor_mock):
    close_end_switch_mock.read.side_effect = lambda:door_controller.close_switch_slot(True)
    door_controller.light_slot(False)
    door_controller.do_all()
    motor_mock.go.assert_not_called()

def test_motor_stops_when_open_end_switch_hit(door_controller,
                                              open_end_switch_mock,
                                              motor_mock):
    open_end_switch_mock.read.side_effect = lambda:door_controller.open_switch_slot(False)
    door_controller.light_slot(True)
    door_controller.open_switch_slot(True)
    door_controller.do_all()
    motor_mock.stop.assert_called_once()

def test_motor_stops_when_close_end_switch_hit(door_controller,
                                               close_end_switch_mock,
                                               motor_mock):
    close_end_switch_mock.read.side_effect = lambda:door_controller.close_switch_slot(False)
    door_controller.light_slot(False)
    door_controller.close_switch_slot(True)
    door_controller.do_all()
    motor_mock.stop.assert_called_once()

def test_night_comes_close_door(door_controller,
                                close_end_switch_mock,
                                motor_mock):
    door_controller.light_slot(True)
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    door_controller.do_all()
    motor_mock.go.assert_called_once_with(+1)

def test_day_comes_open_door(door_controller,
                             open_end_switch_mock,
                             motor_mock):
    door_controller.light_slot(False)
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(True)
    door_controller.do_all()
    motor_mock.go.assert_called_once_with(-1)

def test_day_comes_while_closing_open_door(door_controller,
                                           close_end_switch_mock,
                                           open_end_switch_mock,
                                           motor_mock):
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(True)
    door_controller.do_all()
    motor_mock.go.assert_has_calls([call(+1), call(-1)])

def test_night_comes_while_opening_close_door(door_controller,
                                              close_end_switch_mock,
                                              open_end_switch_mock,
                                              motor_mock):
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(True)
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    door_controller.do_all()
    motor_mock.go.assert_has_calls([call(-1), call(+1)])

def test_reverse_motor_on_stuck_close_end(door_controller,
                                          open_end_switch_mock,
                                          close_end_switch_mock,
                                          motor_mock,
                                          detach_from_end_timeout_ms,
                                          timers):
    open_end_switch_mock.is_on.return_value = False
    close_end_switch_mock.is_on.return_value = True
    door_controller.light_slot(True)
    door_controller.do_all()
    for _ in range(4):
        fake_time_elapsed(timers, detach_from_end_timeout_ms)
    door_controller.do_all()
    motor_mock.go.assert_has_calls([call(-1), call(1), call(-1), call(1), call(-1)])

def test_motor_keeps_on_when_close_switch_opens(door_controller,
                                                open_end_switch_mock,
                                                close_end_switch_mock,
                                                motor_mock,
                                                detach_from_end_timeout_ms,
                                                timers):
    open_end_switch_mock.is_on.return_value = False
    close_end_switch_mock.is_on.return_value = True
    door_controller.light_slot(True)
    door_controller.do_all()
    fake_time_elapsed(timers, detach_from_end_timeout_ms)
    door_controller.close_switch_slot(False)
    door_controller.do_all()
    motor_mock.go.assert_has_calls([call(-1), call(1), call(1)])

def test_reverse_motor_on_stuck_open_end(door_controller,
                                         open_end_switch_mock,
                                         close_end_switch_mock,
                                         motor_mock,
                                         detach_from_end_timeout_ms,
                                         timers):
    open_end_switch_mock.is_on.return_value = True
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    door_controller.do_all()
    for _ in range(3):
        fake_time_elapsed(timers, detach_from_end_timeout_ms)
    door_controller.do_all()
    motor_mock.go.assert_has_calls([call(1), call(-1), call(1), call(-1)])

def test_motor_keeps_on_when_open_switch_opens(door_controller,
                                               open_end_switch_mock,
                                               close_end_switch_mock,
                                               motor_mock,
                                               detach_from_end_timeout_ms,
                                               timers):
    open_end_switch_mock.is_on.return_value = True
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    door_controller.do_all()
    fake_time_elapsed(timers, detach_from_end_timeout_ms)
    door_controller.open_switch_slot(False)
    door_controller.do_all()
    motor_mock.go.assert_has_calls([call(1), call(-1), call(-1)])

def test_reverse_motor_limited_times_on_stuck_end(door_controller,
                                                  open_end_switch_mock,
                                                  close_end_switch_mock,
                                                  motor_mock,
                                                  detach_from_end_timeout_ms,
                                                  timers):
    open_end_switch_mock.is_on.return_value = True
    close_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    door_controller.do_all()
    for _ in range(4):
        fake_time_elapsed(timers, detach_from_end_timeout_ms)
    door_controller.do_all()
    motor_mock.reset_mock()
    fake_time_elapsed(timers, detach_from_end_timeout_ms)
    door_controller.do_all()
    motor_mock.go.assert_not_called()
    motor_mock.stop.assert_called_once()

def test_sleep_after_door_open(door_controller,
                               open_end_switch_mock,
                               sleep_pin_mock):
    open_end_switch_mock.read.side_effect = lambda:door_controller.open_switch_slot(False)
    door_controller.light_slot(True)
    door_controller.open_switch_slot(True)
    door_controller.do_all()
    sleep_pin_mock.value.called_once_with(1)

def test_sleep_after_door_close(door_controller,
                                close_end_switch_mock,
                                sleep_pin_mock):
    close_end_switch_mock.read.side_effect = lambda:door_controller.close_switch_slot(False)
    door_controller.light_slot(False)
    door_controller.close_switch_slot(True)
    door_controller.do_all()
    sleep_pin_mock.value.called_once_with(1)

del sys.modules['machine']
