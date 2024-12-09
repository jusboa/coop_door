from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from .state_machine import StateMachine, State, Signal

class DoorController():
    def __init__(self):
        self.motor = Motor(0, 1)
        self.light_sensor = LightSensor(0)
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
        closed.do_on_entry(lambda m=self.motor : m.stop())\
              .on_signal(self.day).go_to(drive_open)
        self.night = Signal()
        power_on.on_signal(self.night).go_to(drive_close)
        opened.do_on_entry(lambda m=self.motor : m.stop())\
              .on_signal(self.night).go_to(drive_close)
        self.opened_end_switch_on = Signal()
        self.closed_end_switch_on = Signal()
        drive_open.do_on_entry(lambda m=self.motor : m.backward())\
                  .on_signal(self.opened_end_switch_on).go_to(opened)
        drive_close.do_on_entry(lambda m=self.motor : m.forward())\
                   .on_signal(self.closed_end_switch_on).go_to(closed)
        self.state_machine.start()

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
