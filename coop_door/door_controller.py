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
        self.light_sensor.register_day_slot(self.day_slot)
        self.open_switch.register_slot(self.open_switch_slot)
        self.close_switch.register_slot(self.close_switch_slot)
        # State Machine
        self.state_machine = StateMachine('DoorControllerStateMachine')
        power_on = State('power_on', self.state_machine)
        self.state_machine.set_init_state(power_on)
        drive_open = State('drive_open', self.state_machine)
        drive_close = State('drive_close', self.state_machine)
        opened = State('opened', self.state_machine)
        closed = State('closed', self.state_machine)
        self.day = Signal()
        power_on.on_signal(self.day).go_to(drive_open)
        closed.do_on_entry(lambda : self.motor.stop())\
              .on_signal(self.day).go_to(drive_open)
        self.night = Signal()
        power_on.on_signal(self.night).go_to(drive_close)
        opened.do_on_entry(lambda : self.motor.stop())\
              .on_signal(self.night).go_to(drive_close)
        self.opened_end_switch_on = Signal()
        self.closed_end_switch_on = Signal()
        drive_open.do_on_entry(lambda : self.motor.backward())\
                  .on_signal(self.opened_end_switch_on).go_to(opened)
        drive_open.on_timeout(door_move_timeout_ms).go_to(opened)
        drive_open.on_signal(self.night).go_to(drive_close)
        drive_close.do_on_entry(lambda : self.motor.forward())\
                   .on_signal(self.closed_end_switch_on).go_to(closed)
        drive_close.on_timeout(door_move_timeout_ms).go_to(closed)
        drive_close.on_signal(self.day).go_to(drive_open)
        self.timer = Timer(wake_up_period_ms, self._wake_up)
        # Move following into a start() method
        self.state_machine.start()
        self.timer.start()

    def _wake_up(self):
        self.light_sensor.read_light_intensity()
        self.open_switch.read()
        self.close_switch.read()

    def day_slot(self, is_day):
        if (is_day):
            self.state_machine.send_signal(self.day)
        else:
            self.state_machine.send_signal(self.night)

    def open_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.opened_end_switch_on)

    def close_switch_slot(self, is_on):
        if (is_on):
            self.state_machine.send_signal(self.closed_end_switch_on)
