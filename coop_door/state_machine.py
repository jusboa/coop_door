import logging

class Transition():
    def __init__(self, source):
        self.source = source
        self.target = None
        self.action = None

    def go_to(self, target):
        self.target = target
        return target

    def do(self, action):
        self.action = action
        return self

class State():
    def __init__(self, name, parent=None):
        self.name = name
        self.init_state = None
        self.transitions = {}
        self.entry_action = None
        self.exit_action = None
        self.current_state = None
        self.parent_state = parent

    def send_signal(self, signal):
        transition = None
        if signal in self.transitions.keys():
            transition = self.transitions[signal]
        elif self.current_state:
            transition = self.current_state.send_signal(signal)

        if not transition:
            return None

        logging.debug(f'target={transition.target.name}')

        if transition.target and transition.target.parent_state is self:
            self.current_state.exit()
            if transition.action:
                transition.action()
            self.current_state = transition.target
            self.current_state.enter()
            return None
        else:
            return transition

    def on_signal(self, signal):
        self.transitions[signal] = Transition(self)
        return self.transitions[signal]

    def do_on_entry(self, action):
        self.entry_action = action
        return self

    def do_on_exit(self, action):
        self.exit_action = action
        return self

    def enter(self):
        logging.debug(f'entering {self.name}')
        if self.entry_action:
            logging.debug(f'entry action of {self.name}')
            self.entry_action()
        if self.init_state:
            self.current_state = self.init_state
            return self.init_state.enter()
        return self

    def exit(self):
        if self.current_state:
            self.current_state.exit()
        if self.exit_action:
            logging.debug(f'exit action of {self.name}')
            self.exit_action()
        self.current_state = None
        logging.debug(f'leaving {self.name}')

    def set_init_state(self, init_state):
        assert init_state.parent_state is self
        self.init_state = init_state

class Signal():
    pass

class StateMachine(State):
    def __init__(self, name='StateMachine'):
        super().__init__(name)

    def start(self):
        assert self.init_state
        self.enter()
