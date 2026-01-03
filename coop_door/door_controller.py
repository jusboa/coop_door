from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from .state_machine import StateMachine, State, Signal, Choice
from .timer import Timer
from .battery_voltage_sensor import BatteryVoltageSensor
from machine import PWM, Pin, mem32, freq
import logging

logger = logging.getLogger(__name__)

class MotorControl():
    DETACH_FROM_END_TIMEOUT_MS = 2000
    DETACH_TRIAL_MAX = 4
    def __init__(self, start_switch,
                 stop_switch, motor,
                 direction, drive_timeout_ms):
        self.start_switch = start_switch
        self.stop_switch = stop_switch
        self.motor = motor
        self.default_direction = direction
        self.direction = direction
        self.detach_trials = 0
        self.finish_slots = []
        self.drive_timeout_ms = drive_timeout_ms

        # @startuml{motor_control.png}
        # [*] --> idle
        # idle --> active : start_request
        # active --> idle : stop_request
        # state active {
        #   state is_stop_switch_on <<choice>>
        #   [*] --> is_stop_switch_on
        #   is_stop_switch_on --> end : [stop sw on]
        #   is_stop_switch_on --> drive_to_end : [stop sw off]
        #   state drive_to_end {
        #      state is_start_switch_on <<choice>>
        #      state is_max_trials <<choice>>
        #      [*] --> is_start_switch_on
        #      is_start_switch_on --> wait_start_sw_off : [start sw on]
        #      is_start_switch_on --> go : [start sw off]
        #      wait_start_sw_off --> is_max_trials : timeout / ++trials, dir = -dir
        #      is_max_trials --> wait_start_sw_off : [trials <= max]
        #      is_max_trials --> end : [trials > max] : report error
        #      wait_start_sw_off : entry : motor.go(dir)
        #      wait_start_sw_off --> go : start sw off
        #      go : entry : motor.go(dir)
        #      drive_to_end : entry : trials = 0
        #      go --> end : timeout : report error
        #   }
        #   drive_to_end --> end : stop sw on
        #   end : entry : motor.stop(), report finished
        # }
        # @enduml
        self.start_switch_on = Signal('start_switch_on')
        self.start_switch_off = Signal('start_switch_off')
        self.stop_switch_off = Signal('stop_switch_off')
        self.stop_switch_on = Signal('stop_switch_on')
        self.start_request = Signal('start_request')
        self.stop_request = Signal('stop_request')

        self.state_machine = StateMachine('MotorControlStateMachine')

        idle = State('idle', self.state_machine)
        self.state_machine.set_init_state(idle)
        active = State('active', self.state_machine)
        idle.on_signal(self.start_request).go_to(active)
        active.on_signal(self.stop_request).go_to(idle)
        is_stop_switch_on = Choice('is_stop_switch_on', active)
        active.set_init_state(is_stop_switch_on)
        drive_to_end = State('drive_to_end', active)
        end = State('end', active)
        is_start_switch_on = Choice('is_start_switch_on', drive_to_end)
        wait_start_sw_off = State('wait_start_sw_off', drive_to_end)
        go = State('go', drive_to_end)
        is_trials_max = Choice('is_trials_max', drive_to_end)

        is_stop_switch_on.go_to_if(end, self.stop_switch.is_on)
        is_stop_switch_on.go_to_if(drive_to_end, lambda:not self.stop_switch.is_on())
        end.do_on_entry(self._end_entry)
        drive_to_end.on_signal(self.stop_switch_on).go_to(end)
        drive_to_end.set_init_state(is_start_switch_on)
        drive_to_end.do_on_entry(self._clear_detach_trials)
        is_start_switch_on.go_to_if(wait_start_sw_off, self.start_switch.is_on)
        is_start_switch_on.go_to_if(go, lambda:not self.start_switch.is_on())
        wait_start_sw_off.do_on_entry(lambda:self.motor.go(self.direction))
        wait_start_sw_off.on_timeout(MotorControl.DETACH_FROM_END_TIMEOUT_MS)\
            .go_to(is_trials_max).do(lambda:[self._inc_detach_trials(), self._reverse_direction()])
        is_trials_max.go_to_if(wait_start_sw_off, lambda:self.detach_trials <= MotorControl.DETACH_TRIAL_MAX)
        is_trials_max.go_to_if(end, lambda:self.detach_trials > MotorControl.DETACH_TRIAL_MAX)\
            .do(lambda:[self._reset_direction(), logger.debug('Maximum end-detach trials reached.')])
        wait_start_sw_off.on_signal(self.start_switch_off).go_to(go)
        go.do_on_entry(lambda:self.motor.go(self.direction))
        go.on_timeout(self.drive_timeout_ms).do(lambda:logger.debug('Failed to close/open the door in time.')).go_to(end)
        
        self.state_machine.start()

    def _end_entry(self):
        logger.debug('stopping motor')
        self.motor.stop()
        self._report_finished()

    def _report_finished(self):
        for slot in self.finish_slots:
            slot()

    def _inc_detach_trials(self):
        self.detach_trials += 1

    def _clear_detach_trials(self):
        self.detach_trials = 0

    def _reverse_direction(self):
        self.direction = -self.direction

    def _reset_direction(self):
        self.direction = self.default_direction

    def start_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.start_switch_on)
        else:
            self.state_machine.send_signal(self.start_switch_off)

    def stop_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.stop_switch_on)
        else:
            self.state_machine.send_signal(self.stop_switch_off)

    def start(self):
        logger.debug('start')
        self.state_machine.send_signal(self.start_request)

    def stop(self):
        logger.debug('stop')
        self.state_machine.send_signal(self.stop_request)

    def register_finish_slot(self, slot):
        self.finish_slots.append(slot)

class DoorController():
    def __init__(self, wake_up_period_ms=100,
                 door_move_timeout_ms=30000):
        self.motor = Motor(14, 15, 9, self.motor_voltage)
        self.light_sensor = LightSensor(28, 0)
        self.light_sensor.wakeup()
        self.open_switch = EndSwitch(1)
        self.close_switch = EndSwitch(2)
        self.light_sensor.register_light_slot(self.light_slot)
        self.open_switch.register_slot(self.open_switch_slot)
        self.close_switch.register_slot(self.close_switch_slot)
        self.drive_open_controller = MotorControl(self.close_switch,
                                                  self.open_switch,
                                                  self.motor,
                                                  -1,
                                                  door_move_timeout_ms)
        self.drive_close_controller = MotorControl(self.open_switch,
                                                   self.close_switch,
                                                   self.motor,
                                                   +1,
                                                   door_move_timeout_ms)
        self.sleep_pin = Pin(22, Pin.OUT)
        self.sleep_pin.value(0)
        self.voltage_sensor = BatteryVoltageSensor(26)
        self.voltage_sensor.register_slot(self.battery_voltage_slot)
        self.battery_voltage_v = None

        freq(48000000)

        # State Machine
        # @startuml{door_controller.png} 
        # state start
        # [*] --> start
        # start --> day : light
        # start --> night : dark
        # day --> night : dark
        # state day {
        #    state "finish" as finish_day
        #    [*] --> open_door
        #    open_door : entry: start motor_control
        #    open_door : exit : stop motor_control
        #    open_door --> finish_day : finished
        #    finish_day : entry : sleep
        # }
        # night --> day : light
        # state night {
        #    state "finish" as finish_night
        #    [*] --> close_door
        #    close_door : entry : start motor_control
        #    close_door : exit : stop motor_control
        #    close_door --> finish_night : finished
        #    finish_night : entry : sleep
        # }
        # @enduml
        self.state_machine = StateMachine('DoorControllerStateMachine')
        start = State('start', self.state_machine)
        self.state_machine.set_init_state(start)

        day = State('day', self.state_machine)
        open_door = State('open_door', day)
        finish_day = State('finish_day', day)
        day.set_init_state(open_door)

        night = State('night', self.state_machine)
        close_door = State('close_door', night)
        finish_night = State('finish_night', night)
        night.set_init_state(close_door)

        self.light = Signal('light')
        self.dark = Signal('dark')
        self.finished = Signal('finished')

        self.timer = Timer(wake_up_period_ms, self._wakeup)

        start.do_on_entry(lambda:( self.timer.start(), logger.info('Starting door controller')))
        start.on_signal(self.light).go_to(day)
        day.on_signal(self.dark).go_to(night)
        open_door.on_signal(self.finished).go_to(finish_day)
        open_door.do_on_entry(self.drive_open_controller.start)
        open_door.do_on_exit(self.drive_open_controller.stop)
        finish_day.do_on_entry(self._sleep)

        start.on_signal(self.dark).go_to(night)
        night.on_signal(self.light).go_to(day)
        close_door.on_signal(self.finished).go_to(finish_night)
        close_door.do_on_entry(self.drive_close_controller.start)
        close_door.do_on_exit(self.drive_close_controller.stop)
        finish_night.do_on_entry(self._sleep)

        self.drive_close_controller.register_finish_slot(
            lambda:self.state_machine.send_signal(self.finished))
        self.drive_open_controller.register_finish_slot(
            lambda:self.state_machine.send_signal(self.finished))

    def _sleep(self):
        # Do PWM on sleep pin for the sleep circuit not to miss it. It detects
        # the rising edge, minimum pulse width is 100ns.
        PWM(self.sleep_pin, freq=100, duty_u16=round(0.5*0xFFFF))

    def _wakeup(self):
        self.light_sensor.read()
        self.voltage_sensor.read()
        self.drive_open_controller.state_machine.process_signal()
        self.drive_close_controller.state_machine.process_signal()
        self.state_machine.process_signal()

    def do_all(self):
        anything_to_do = True
        while anything_to_do:
            self.drive_open_controller.state_machine.process_signal()
            self.drive_close_controller.state_machine.process_signal()
            self.state_machine.process_signal()
            anything_to_do = self.drive_open_controller.state_machine.anything_to_do()\
                or self.drive_close_controller.state_machine.anything_to_do()\
                or self.state_machine.anything_to_do()

    def light_slot(self, is_light):
        if (is_light):
            self.state_machine.send_signal(self.light)
        else:
            self.state_machine.send_signal(self.dark)

    def open_switch_slot(self, is_on):
        logger.debug(f'open switch = {is_on}')
        self.drive_open_controller.stop_switch_slot(is_on)
        self.drive_close_controller.start_switch_slot(is_on)

    def close_switch_slot(self, is_on):
        logger.debug(f'close switch = {is_on}')
        self.drive_open_controller.start_switch_slot(is_on)
        self.drive_close_controller.stop_switch_slot(is_on)

    def battery_voltage_slot(self, voltage_v):
        self.battery_voltage_v = voltage_v
        #logger.debug(f'battery voltage = {voltage_v:.3f} V')

    def motor_voltage(self):
        return self.battery_voltage_v

    def start(self):
        self.state_machine.start()
