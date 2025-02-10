#import logging
from .timer import Timer

class Transition():
    def __init__(self, source, target=None, action=None):
        self.source = source
        self.target = target
        self.action = action
        self.condition = None
        self.else_target = None

    def go_to(self, target, condition=None, else_target=None):
        self.condition = condition
        self.else_target = else_target
        self.target = target

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
        self.timeout = Signal('timeout')
        self.timer = None
        self.entered = Signal('entered')

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
        #print(f'entering {self.name}')
        if self.timer:
            #print(f'starting the {self.name} state timer')
            self.timer.start()
        if self.parent:
            self.parent.current_state = self
        if self.entry_action:
            #logging.debug(f'entry action of {self.name}')
            #print(f'entry action of {self.name}')
            self.entry_action()
        #self.send_signal(self.entered)
        self._find_topmost_parent().send_signal(self.entered)

    def start(self):
        #print(f'entering {self.name}')
        self.enter()
        if self.init_state:
            self.init_state.start()

    def exit(self):
        if self.current_state:
            self.current_state.exit()
        if self.timer:
            self.timer.stop()
        if self.exit_action:
            #logging.debug(f'exit action of {self.name}')
            self.exit_action()
        self.current_state = None
        #print(f'leaving {self.name}')

    def set_init_state(self, init_state):
        assert init_state.parent is self
        self.init_state = init_state

    def on_timeout(self, timeout_ms):
        self.timer = Timer(timeout_ms,
                           #lambda : self.send_signal(self.timeout),
                           lambda : self._find_topmost_parent().send_signal(self.timeout),
                           Timer.SINGLE_SHOT)
        self.transitions[self.timeout] = Transition(self)
        return self.transitions[self.timeout]

    def _try_do_transition(self, transition):
        ''' Try to perform the state transtion.
        Return None if the transition has been done. Return the original
        transition if not done.
        '''
        # Try to find a common source and target parent.
        if transition.condition is not None:
            target = transition.target if transition.condition() else transition.else_target
        else:
            target = transition.target
        target_path = [target]
        while target and target.parent is not self.parent:
            target = target.parent
            # Keep track of parents to call entry actions
            # when entering a target state.
            target_path.append(target)
        if target:
            # Found a common source and target parent.
            # Exit the source state.
            self.exit()
            # Do the transition action.
            if transition.action:
                #print(f'{transition.source.name}->{transition.target.name} transition action')
                transition.action()
            # Enter the target state and all its parents.
            # Reverse it to go down in hieararchy - from parent to child
            target_path.reverse()
            for state in target_path[:-1]:
                state.enter()
            target_path[-1].start()

            return None
        else:
            # No common parent of source and target found.
            # Kick it up.
            return transition

    def send_signal(self, signal):
        #print(f'signal {signal.name} in state {self.name}')
        if signal in self.transitions.keys():
            return self._try_do_transition(self.transitions[signal])
        elif self.current_state:
            # Try active substate
            transition = self.current_state.send_signal(signal)
            if transition:
                # Retry with ammended transition
                return self._try_do_transition(transition)
        return None

    def _find_topmost_parent(self):
        state = self
        while state:
            if state.parent is None:
                return state
            state = state.parent
        return None

class Signal():
    def __init__(self, name='noname'):
        self.name = name

class StateMachine(State):
    def __init__(self, name='StateMachine'):
        super().__init__(name)

    def start(self):
        assert self.init_state
        super().start()

class Choice(State):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)

    def go_to(self, condition, if_true_target, else_target):
        self.on_signal(self.entered).go_to(condition, if_true_target, else_target)
