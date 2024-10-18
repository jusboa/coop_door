from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed

class DoorStateMachine(StateMachine):
    power_on = State(initial=True)
    drive_open = State()
    drive_close = State()
    opened = State()
    closed = State()
    day = power_on.to(drive_open) | closed.to(drive_open)
    night = power_on.to(drive_close) | opened.to(drive_close)
    opened_end_switch_on = drive_open.to(opened)
    closed_end_switch_on = drive_close.to(closed)

    def __init__(self, motor):
        super().__init__()
        self.motor = motor

    def on_enter_drive_open(self):
        self.motor.backward()

    def on_enter_drive_close(self):
        self.motor.forward()

    def on_enter_opened(self):
        self.motor.stop()

    def on_enter_closed(self):
        self.motor.stop()

class DoorController():
    def __init__(self):
        self.motor = Motor(0, 1)
        self.light_sensor = LightSensor(0)
        self.open_switch = EndSwitch(1)
        self.close_switch = EndSwitch(2)

        self.state_machine = DoorStateMachine(self.motor)
        self.light_sensor.register_day_slot(self.day_slot)
        self.open_switch.register_slot(self.open_switch_slot)
        self.close_switch.register_slot(self.close_switch_slot)

    def day_slot(self, is_day):
        try:
            if (is_day):
                self.state_machine.day()
            else:
                self.state_machine.night()
        except TransitionNotAllowed:
            pass

    def open_switch_slot(self, is_on):
        if (is_on):
            try:
                self.state_machine.opened_end_switch_on()
            except TransitionNotAllowed:
                pass

    def close_switch_slot(self, is_on):
        if (is_on):
            try:
                self.state_machine.closed_end_switch_on()
            except TransitionNotAllowed:
                pass

