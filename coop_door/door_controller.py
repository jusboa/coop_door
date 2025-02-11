from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from .state_machine import StateMachine, State, Signal, Choice
from .timer import Timer

class MotorControl():
    DETACH_FROM_END_TIMEOUT_MS = 2000
    DETACH_TRIAL_MAX = 4
    ERROR_TIMEOUT_MS = 3600 * 1000
    def __init__(self, start_switch,
                 stop_switch, motor,
                 direction, drive_timeout_ms=10000):
        self.start_switch = start_switch
        self.stop_switch = stop_switch
        self.motor = motor
        self.direction = direction
        self.detach_trials = 0

        # @startuml{motor_control.png}
        # [*] --> idle
        # idle --> active : start_request
        # active --> idle : stop_request
        # state error
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
        #      is_max_trials --> error : [trials > max]
        #      wait_start_sw_off : entry : motor.go(dir)
        #      wait_start_sw_off --> go : start sw off
        #      go : entry : motor.go(dir)
        #      drive_to_end : entry : trials = 0
        #   }
        #   drive_to_end --> end : stop sw on
        #   drive_to_end --> end : timeout
        #   end : entry : motor.stop()
        #   error --> active : timeout
        #   error --> idle : stop_request
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
        error = State('error', self.state_machine)

        is_stop_switch_on.go_to_if(end, self.stop_switch.is_on)
        is_stop_switch_on.go_to_if(drive_to_end, lambda:not self.stop_switch.is_on())
        end.do_on_entry(lambda:self.motor.stop())
        drive_to_end.on_signal(self.stop_switch_on).go_to(end)
        drive_to_end.set_init_state(is_start_switch_on)
        drive_to_end.do_on_entry(lambda:self._clear_detach_trials)
        is_start_switch_on.go_to_if(wait_start_sw_off, self.start_switch.is_on)
        is_start_switch_on.go_to_if(go, lambda:not self.start_switch.is_on())
        wait_start_sw_off.do_on_entry(lambda:self.motor.go(self.direction))
        wait_start_sw_off.on_timeout(MotorControl.DETACH_FROM_END_TIMEOUT_MS)\
            .go_to(is_trials_max).do(lambda:[self._inc_detach_trials(), self._reverse_direction()])
        is_trials_max.go_to_if(wait_start_sw_off, lambda:self.detach_trials < MotorControl.DETACH_TRIAL_MAX)
        is_trials_max.go_to_if(error, lambda:self.detach_trials >= MotorControl.DETACH_TRIAL_MAX)
        wait_start_sw_off.on_signal(self.stop_switch_off).go_to(go)
        error.do_on_entry(lambda:[self.motor.stop(), print('Maximum end-detach trials reached.')])
        error.on_timeout(MotorControl.ERROR_TIMEOUT_MS).go_to(active)
        error.on_signal(self.stop_request).go_to(idle)
        go.do_on_entry(lambda:self.motor.go(self.direction))
        drive_to_end.on_timeout(drive_timeout_ms).go_to(end)
        
        self.state_machine.start()

    def _inc_detach_trials(self):
        self.detach_trials += 1

    def _clear_detach_trials(self):
        self.detach_trials = 0

    def _reverse_direction(self):
        self.direction = -self.direction

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
        self.state_machine.send_signal(self.start_request)

    def stop(self):
        self.state_machine.send_signal(self.stop_request)

class DoorController():
    def __init__(self, wake_up_period_ms=100,
                 door_move_timeout_ms=10000):
        self.motor = Motor(2, 3, 6)
        self.light_sensor = LightSensor(2, 0)
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
        # State Machine
        # @startuml{door_controller.png} 
        # state start
        # [*] --> start
        # start --> day : light
        # start --> night : dark
        # day --> night : dark
        # day : entry : open door
        # night --> day : light
        # night : entry : close door
        # @enduml
        self.state_machine = StateMachine('DoorControllerStateMachine')
        start = State('start', self.state_machine)
        self.state_machine.set_init_state(start)

        day = State('day', self.state_machine)
        day.do_on_entry(self.drive_open_controller.start)
        day.do_on_exit(self.drive_open_controller.stop)

        night = State('night', self.state_machine)
        night.do_on_entry(self.drive_close_controller.start)
        night.do_on_exit(self.drive_close_controller.stop)

        self.light = Signal('light')
        self.dark = Signal('dark')

        start.do_on_entry(lambda:self.timer.start())
        start.on_signal(self.light).go_to(day)
        start.on_signal(self.dark).go_to(night)
        day.on_signal(self.dark).go_to(night)
        night.on_signal(self.light).go_to(day)

        self.timer = Timer(wake_up_period_ms, self._wake_up)

    def _wake_up(self):
        self.light_sensor.read_light_intensity()

    def light_slot(self, is_light):
        if (is_light):
            self.state_machine.send_signal(self.light)
        else:
            self.state_machine.send_signal(self.dark)

    def open_switch_slot(self, is_on):
        self.drive_open_controller.start_switch_slot(is_on)
        self.drive_close_controller.stop_switch_slot(is_on)

    def close_switch_slot(self, is_on):
        self.drive_open_controller.stop_switch_slot(is_on)
        self.drive_close_controller.start_switch_slot(is_on)

    def start(self):
        self.state_machine.start()
