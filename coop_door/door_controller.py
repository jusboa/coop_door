from .dcmotor_drive import Motor
from .light_sensor import LightSensor
from .end_switch import EndSwitch
from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed

class DoorStateMachine(StateMachine):
    power_on = State(initial=True)
    drive_open = State()
    opened = State(final=True)
    day = power_on.to(drive_open)
    opened_end_switch_on = drive_open.to(opened)

    def __init__(self, motor):
        super().__init__()
        self.motor = motor

    def on_enter_drive_open(self):
        self.motor.backward()

    def on_enter_opened(self):
        self.motor.stop()


class DoorController():
    def __init__(self):
        self.motor = Motor(0, 1)
        self.light_sensor = LightSensor(0)
        self.open_switch = EndSwitch(1)
        self.close_switch = EndSwitch(2)

        self.state_machine = DoorStateMachine(self.motor)

    def start(self):
        if self.light_sensor.is_day():
            self.motor.backward()
        else:
            self.motor.forward()

    def run(self):
        try:
            if self.light_sensor.is_day():
                self.state_machine.day()
        except TransitionNotAllowed:
            pass
        try:
            if self.open_switch.is_on():
                self.state_machine.opened_end_switch_on()
        except TransitionNotAllowed:
            pass
        
