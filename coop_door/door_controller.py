from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from .state_machine import StateMachine, State, Signal, Choice
from .timer import Timer

class DoorController():
    END_SWITCH_OFF_TIMEOUT_MS = 1000
    def __init__(self, wake_up_period_ms=100,
                 door_move_timeout_ms=10000):
        self.motor = Motor(2, 3, 6)
        self.light_sensor = LightSensor(2, 0)
        self.open_switch = EndSwitch(1)
        self.close_switch = EndSwitch(2)
        self.light_sensor.register_light_slot(self.light_slot)
        self.open_switch.register_slot(self.open_switch_slot)
        self.close_switch.register_slot(self.close_switch_slot)
        # State Machine
        # @startuml
        # state is_light <<choice>>
        # [*] --> is_light
        # is_light --> day : [light]
        # is_light --> night : [dark]
        # state day {
        #    state is_open_switch_on <<choice>>
        #    [*] --> is_open_switch_on
        #    is_open_switch_on --> opened : [switch on]
        #    is_open_switch_on --> drive_open : [switch off]
        #    drive_open : entry : motor go(-1)
        #    drive_open --> opened : switch on
        #    drive_open --> opened : timeout
        #    opened : entry : motor stop
        # }
        # day --> night : dark
        # state night {
        #    state is_close_switch_on <<choice>>
        #    [*] --> is_close_switch_on
        #    is_close_switch_on --> closed : [switch on]
        #    is_close_switch_on --> drive_close : [switch off]
        #    drive_close : entry : motor go(+1)
        #    drive_close --> closed : switch on
        #    drive_close --> closed : timeout
        #    closed : entry : motor stop
        # }
        # night --> day : light
        # @enduml
        self.state_machine = StateMachine('DoorControllerStateMachine')
        start = State('start', self.state_machine)
        self.state_machine.set_init_state(start)

        day = State('day', self.state_machine)
        is_open_switch_on = Choice('is_open_switch_on', day)
        drive_open = State('drive_open', day)
        opened = State('opened', day)

        night = State('night', self.state_machine)
        is_close_switch_on = Choice('is_close_switch_on', night)
        drive_close = State('drive_close', night)
        closed = State('closed', night)

        self.light = Signal('light')
        self.dark = Signal('dark')
        self.open_end_switch_on = Signal('open_switch_on')
        self.open_end_switch_off = Signal('open_switch_off')
        self.close_end_switch_off = Signal('close_end_switch_off')
        self.closed_end_switch_on = Signal('close_end_switch_on')

        start.do_on_entry(lambda:self.timer.start())
        start.on_signal(self.light).go_to(day)
        start.on_signal(self.dark).go_to(night)

        day.set_init_state(is_open_switch_on)
        is_open_switch_on.go_to(opened, self.open_switch.is_on, drive_open)
        opened.do_on_entry(lambda : self.motor.stop())
        drive_open.do_on_entry(lambda : self.motor.go(-1))\
                  .on_signal(self.open_end_switch_on).go_to(opened)
        drive_open.on_timeout(door_move_timeout_ms).go_to(opened)
        day.on_signal(self.dark).go_to(night)


        night.set_init_state(is_close_switch_on)
        is_close_switch_on.go_to(closed, self.close_switch.is_on, drive_close)
        closed.do_on_entry(lambda : self.motor.stop())
        drive_close.do_on_entry(lambda : self.motor.go(+1))\
                   .on_signal(self.closed_end_switch_on).go_to(closed)
        drive_close.on_timeout(door_move_timeout_ms).go_to(closed)
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
        if (is_on):
            self.state_machine.send_signal(self.open_end_switch_on)
        else:
            self.state_machine.send_signal(self.open_end_switch_off)

    def close_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.closed_end_switch_on)
        else:
            self.state_machine.send_signal(self.close_end_switch_off)

    def start(self):
        self.state_machine.start()
