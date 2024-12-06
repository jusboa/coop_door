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
        self.parent = parent

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
        if self.parent:
            self.parent.current_state = self
        if self.entry_action:
            logging.debug(f'entry action of {self.name}')
            self.entry_action()

    def start(self):
        self.enter()
        if self.init_state:
            return self.init_state.start()
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
        assert init_state.parent is self
        self.init_state = init_state

class Signal():
    pass

class StateMachine(State):
    def __init__(self, name='StateMachine'):
        super().__init__(name)

    def start(self):
        assert self.init_state
        super().start()

    def send_signal(self, signal):
        # Find a state that handles the signal.
        transition = None
        state = self.current_state
        while state:
            if signal in state.transitions.keys():
                transition = state.transitions[signal]
                break
            state = state.current_state

        if not transition:
            # Signal is not handled by any of active states.
            return None

        source = transition.source
        target = transition.target
        common_parent = None
        target_path = [target]
        while source:
            if source.parent is target.parent:
                common_parent = target.parent
                break
            target = target.parent
            target_path.append(target)
            if not target:
                target = transition.target
                target_path = [target]
                source = source.parent

        assert common_parent, f'Transition source {transition.source} and target \
        {transition.target} must have a common parent - at least the state machine.'
        source.exit()
        if transition.action:
            transition.action()
        for state in target_path[:0:-1]:
            state.enter()
        target_path[0].start()
            


