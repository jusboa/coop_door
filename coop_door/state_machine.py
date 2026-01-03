import logging
from .timer import Timer

logger = logging.getLogger(__name__)

def _find_common_parent(state1, state2):
    ''' Find a common parent of two state.
    Return None if not common parent found 
    '''
    parent1 = state1.parent
    parent2 = state2.parent
    while parent1 is not None:
        while parent2 is not None:
            if parent1 == parent2:
                return parent1
            parent2 = parent2.parent
        parent1 = parent1.parent
        parent2 = state2.parent
    return None

class Transition():
    def __init__(self, source, target=None, action=None):
        self.source = source
        self.target = target
        self.action = action
        self.condition = None

    def go_to(self, target, condition=None):
        self.condition = condition
        self.target = target
        return self

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
        logger.debug(f'entering {self.name}')
        if self.timer:
            logger.debug(f'starting the {self.name} state timer')
            self.timer.start()
        if self.parent:
            self.parent.current_state = self
        if self.entry_action:
            logger.debug(f'entry action of {self.name}')
            logger.debug(f'entry action of {self.name}')
            self.entry_action()

    def start(self):
        logger.debug(f'entering {self.name}')
        self.enter()
        if self.init_state:
            self.init_state.start()

    def exit(self):
        if self.current_state:
            self.current_state.exit()
        if self.timer:
            logger.debug(f'stopping the {self.name} state timer')
            self.timer.stop()
        if self.exit_action:
            logger.debug(f'exit action of {self.name}')
            self.exit_action()
        self.current_state = None
        logger.debug(f'leaving {self.name}')

    def set_init_state(self, init_state):
        assert init_state.parent is self
        self.init_state = init_state

    def on_timeout(self, timeout_ms):
        self.timer = Timer(timeout_ms,
                           lambda : self.send_signal(self.timeout),
                           Timer.SINGLE_SHOT)
        self.transitions[self.timeout] = Transition(self)
        return self.transitions[self.timeout]

    def send_signal(self, signal):
        ''' Try to handle the given signal.
        Check if state cares about the signal. Exit
        the state and its substates and parents if jumping up in
        the hierarchy. Do the transition. Enter target state and
        its parents if they are not in active branch.
        '''
        if signal in self.transitions.keys():
            logger.debug(f'signal {signal.name} in state {self.name}')
            target = self.transitions[signal].target
            # Transition condition
            if self.transitions[signal].condition is not None\
               and not self.transitions[signal].condition():
                return False

            common_parent = _find_common_parent(self, target)

            # Exit
            common_parent.current_state.exit()

            # Transition
            if self.transitions[signal].action:
                self.transitions[signal].action()

            # Enter
            target_path = [target]
            while target.parent is not common_parent:
                target = target.parent
                # Keep track of parents to call entry actions
                # when entering a target state.
                target_path.append(target)
            target_path.reverse()
            for state in target_path[:-1]:
                state.enter()
            target_path[-1].start()

            return True
        else:
            return False

class Signal():
    def __init__(self, name='noname'):
        self.name = name

class StateMachine(State):
    def __init__(self, name='StateMachine'):
        super().__init__(name)
        self.signal_stack = []

    def start(self):
        assert self.init_state
        super().start()

    def send_signal(self, signal):
        self.signal_stack.append(signal)

    def process_signal(self):
        ''' Handle single signal in queue.
        Process the oldest signal from queue.
        Go through active state machine branch, try find the state
        that accepts the given signal.
        '''
        if self.anything_to_do():
            signal = self.signal_stack.pop(0)
            state = self.current_state
            while state is not None:
                if state.send_signal(signal):
                    return True
                state = state.current_state
        return False

    def anything_to_do(self):
        return len(self.signal_stack) > 0

class Choice(State):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.entered = []

    def go_to_if(self, target, condition):
        self.entered.append(Signal(f'entered #{len(self.entered)}'))
        return self.on_signal(self.entered[-1]).go_to(target, condition)

    def enter(self):
        super().enter()
        for s in self.entered:
            self.send_signal(s)
