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
def detach_from_end_timeout_ms():
    return 2000

@pytest.fixture
def voltage_sensor_mock():
    return MagicMock()

@pytest.fixture
def refresh_inputs_period_ms():
    return 123

@pytest.fixture
def motor_drive_timeout_ms():
    return 32555

refresh_inputs_callback = None

@pytest.fixture
def door_controller_factory(light_sensor_mock,
                            close_end_switch_mock,
                            open_end_switch_mock,
                            motor_mock,
                            timers,
                            timer_mock_factory,
                            sleep_pin_mock,
                            voltage_sensor_mock,
                            refresh_inputs_period_ms,
                            timer_mock,
                            motor_drive_timeout_ms):
    def make_door_controller():
        with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
              patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
              patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
              patch('coop_door.coop_door.state_machine.Timer') as StateTimer_mock,
              patch('coop_door.coop_door.door_controller.Pin') as Pin_mock,
              patch('coop_door.coop_door.door_controller.BatteryVoltageSensor') as VoltageSensor_mock,
              patch('coop_door.coop_door.door_controller.Timer') as Timer_mock):
            Timer_mock.return_value = timer_mock
            VoltageSensor_mock.return_value = voltage_sensor_mock
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
            controller = DoorController(refresh_inputs_period_ms,
                                        motor_drive_timeout_ms)
            timers.extend([
                ( return_value[i],
                  StateTimer_mock.call_args_list[i].args[0],
                  StateTimer_mock.call_args_list[i].args[1] ) \
                for i in range(len(StateTimer_mock.call_args_list))])
            global refresh_inputs_callback
            refresh_inputs_callback = Timer_mock.call_args.args[1]
            return controller
    return make_door_controller

@pytest.fixture
def door_controller(door_controller_factory):
    c = door_controller_factory()
    c.start()
    return c

def test_hardware_wiring():
    with (patch('coop_door.coop_door.door_controller.Motor') as Motor_mock,
          patch('coop_door.coop_door.door_controller.LightSensor') as LightSensor_mock,
          patch('coop_door.coop_door.door_controller.EndSwitch') as EndSwitch_mock,
          patch('coop_door.coop_door.door_controller.Pin') as Pin_mock,
          patch('coop_door.coop_door.door_controller.BatteryVoltageSensor') as VoltageSensor_mock):
        Pin_mock.OUT = 333
        d = DoorController()
        Motor_mock.assert_called_once_with(14, 15, 9, d.motor_voltage)
        EndSwitch_mock.assert_has_calls([call(OPEN_END_SWITCH_PIN),
                                         call(CLOSE_END_SWITCH_PIN)])
        LightSensor_mock.assert_called_once_with(28, 0)
        # Sleep pin
        Pin_mock.assert_called_once_with(22, 333)
        VoltageSensor_mock.assert_called_once_with(26)

def test_light_sensor_is_woken_up_on_init(door_controller,
                                          light_sensor_mock):
    light_sensor_mock.wakeup.assert_called_once()

def test_refresh_timer_config(door_controller, refresh_inputs_period_ms):
    with patch('coop_door.coop_door.door_controller.Timer') as Timer_mock:
        d = DoorController(refresh_inputs_period_ms)
        d.start()
        Timer_mock.assert_called_once()
        assert Timer_mock.call_args.args[0] == refresh_inputs_period_ms

def test_refresh_inputs(door_controller,
                        timer_mock,
                        light_sensor_mock,
                        voltage_sensor_mock):
        timer_mock.start.assert_called_once()
        n = 3
        for _ in range(n):
            refresh_inputs_callback()
        assert light_sensor_mock.read.call_count == n
        assert voltage_sensor_mock.read.call_count == n

def test_register_light_slot(door_controller, light_sensor_mock):
    light_sensor_mock.register_light_slot.assert_called_once_with(door_controller.light_slot)

def test_register_open_end_switch_slot(door_controller, open_end_switch_mock):
    open_end_switch_mock.register_slot.assert_called_once_with(door_controller.open_switch_slot)

def test_register_close_end_switch_slot(door_controller, close_end_switch_mock):
    close_end_switch_mock.register_slot.assert_called_once_with(door_controller.close_switch_slot)

def test_voltage_sensor_slot(door_controller, voltage_sensor_mock):
    voltage_sensor_mock.register_slot.assert_called_once_with(door_controller.battery_voltage_slot)
    
def test_day_on_power_up_open_door(door_controller_factory,
                                   open_end_switch_mock,
                                   close_end_switch_mock,
                                   motor_mock):
    open_end_switch_mock.is_on.return_value = False
    close_end_switch_mock.is_on.return_value = False
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
                                      open_end_switch_mock,
                                      motor_mock):
    close_end_switch_mock.is_on.return_value = False
    open_end_switch_mock.is_on.return_value = False
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
                                open_end_switch_mock,
                                motor_mock):
    open_end_switch_mock.is_on.return_value = True
    door_controller.light_slot(True)
    door_controller.do_all()
    close_end_switch_mock.is_on.return_value = False
    open_end_switch_mock.is_on.return_value = False
    door_controller.light_slot(False)
    door_controller.do_all()
    motor_mock.go.assert_called_once_with(+1)

def test_day_comes_open_door(door_controller,
                             open_end_switch_mock,
                             close_end_switch_mock,
                             motor_mock):
    close_end_switch_mock.is_on.return_value = True
    door_controller.light_slot(False)
    door_controller.do_all()
    open_end_switch_mock.is_on.return_value = False
    close_end_switch_mock.is_on.return_value = False
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

def test_sleep_pin_is_disabled_on_init(door_controller,
                                       sleep_pin_mock):
    sleep_pin_mock.value.assert_called_once_with(0)

def test_sleep_after_door_open(door_controller,
                               open_end_switch_mock,
                               sleep_pin_mock):
    with (patch('coop_door.coop_door.door_controller.PWM') as PWM_mock):
        open_end_switch_mock.read.side_effect = lambda:door_controller.open_switch_slot(False)
        door_controller.light_slot(True)
        door_controller.open_switch_slot(True)
        door_controller.do_all()
        PWM_mock.assert_called_once_with(sleep_pin_mock, freq=100, duty_u16=round(0.5 * 65535))

def test_sleep_after_door_close(door_controller,
                                close_end_switch_mock,
                                sleep_pin_mock):
    with (patch('coop_door.coop_door.door_controller.PWM') as PWM_mock):
        close_end_switch_mock.read.side_effect = lambda:door_controller.close_switch_slot(False)
        door_controller.light_slot(False)
        door_controller.close_switch_slot(True)
        door_controller.do_all()
        PWM_mock.assert_called_once_with(sleep_pin_mock, freq=100, duty_u16=round(0.5 * 65535))

del sys.modules['machine']
