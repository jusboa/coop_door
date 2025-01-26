from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from .state_machine import StateMachine, State, Signal
from .timer import Timer

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
        # State Machine
        # @startuml
        # [*] --> power_on
        # power_on --> day : light
        # state day {
        #    [*] --> drive_open
        #    drive_open : entry : motor backward
        #    drive_open --> opened : opened_end_switch_on
        #    drive_open --> opened : timeout
        #    opened : entry : motor stop
        # }
        # day --> night : dark
        # power_on --> night : dark
        # state night {
        #    [*] --> drive_close
        #    drive_close : entry : motor forward
        #    drive_close --> closed : closed_end_switch_on
        #    drive_close --> closed : timeout
        #    closed : entry : motor stop
        # }
        # night --> day : light
        # @enduml
        self.state_machine = StateMachine('DoorControllerStateMachine')
        power_on = State('power_on', self.state_machine)
        self.state_machine.set_init_state(power_on)
        day = State('day', self.state_machine)
        night = State('night', self.state_machine)
        drive_open = State('drive_open', day)
        day.set_init_state(drive_open)
        drive_close = State('drive_close', night)
        night.set_init_state(drive_close)
        opened = State('opened', day)
        closed = State('closed', night)
        self.light = Signal()
        power_on.on_signal(self.light).go_to(day)
        closed.do_on_entry(lambda : self.motor.stop())
        night.on_signal(self.light).go_to(day)
        self.dark = Signal()
        power_on.on_signal(self.dark).go_to(night)
        opened.do_on_entry(lambda : self.motor.stop())
        day.on_signal(self.dark).go_to(night)
        self.opened_end_switch_on = Signal()
        self.closed_end_switch_on = Signal()
        drive_open.do_on_entry(lambda : self.motor.backward())\
                  .on_signal(self.opened_end_switch_on).go_to(opened)
        drive_open.on_timeout(door_move_timeout_ms).go_to(opened)
        drive_close.do_on_entry(lambda : self.motor.forward())\
                   .on_signal(self.closed_end_switch_on).go_to(closed)
        drive_close.on_timeout(door_move_timeout_ms).go_to(closed)
        self.timer = Timer(wake_up_period_ms, self._wake_up)
        # Move following into a start() method
        self.state_machine.start()
        self.timer.start()

    def _wake_up(self):
        self.light_sensor.read_light_intensity()
        self.open_switch.read()
        self.close_switch.read()

    def light_slot(self, is_light):
        if (is_light):
            self.state_machine.send_signal(self.light)
        else:
            self.state_machine.send_signal(self.dark)

    def open_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.opened_end_switch_on)

    def close_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.closed_end_switch_on)
