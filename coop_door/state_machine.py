""" Finite state machine. """
import logging
from .timer import Timer

logger = logging.getLogger(__name__)

def _find_common_parent(state1, state2):
    """ Find a common parent of two state.
    Return None if not common parent found 
    """
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
    """ State transition
    Transition between the two states with an action to perform
    on transition.
    """
    def __init__(self, source, target=None, action=None):
        self.source = source
        self.target = target
        self.action = action
        self.condition = None

    def go_to(self, target, condition=None):
        """ Define the target state with an optional
        transition condition.
        """
        self.condition = condition
        self.target = target
        return self

    def do(self, action):
        """ Specify the transition action. """
        self.action = action
        return self

class State():
    # pylint: disable=too-many-instance-attributes
    """ Finite state machine state.
    Hook the transition to another state.
    Define entry, exit, timeout actions.
    Feed signals with send_signal.
    """
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
        """ Create a transition triggerred by a signal. """
        self.transitions[signal] = Transition(self)
        return self.transitions[signal]

    def do_on_entry(self, action):
        """ Specify the state entry action. """
        self.entry_action = action
        return self

    def do_on_exit(self, action):
        """ Specify the state exit action. """
        self.exit_action = action
        return self

    def enter(self):
        """ Enter the state.
        Entry action is performed. Timer is started.
        """
        logger.debug('entering %s', self.name)
        if self.timer:
            logger.debug('starting the %s state timer', self.name)
            self.timer.start()
        if self.parent:
            self.parent.current_state = self
        if self.entry_action:
            logger.debug('entry action of %s', self.name)
            self.entry_action()

    def start(self):
        """ Start the state.
        Enter the state and all initial substates.
        """
        logger.debug('entering %s', self.name)
        self.enter()
        if self.init_state:
            self.init_state.start()

    def exit(self):
        """ Exit the state.
        Exit action is performed. Timer is stopped.
        """
        if self.current_state:
            self.current_state.exit()
        if self.timer:
            logger.debug('stopping the %s state timer', self.name)
            self.timer.stop()
        if self.exit_action:
            logger.debug('exit action of %s', self.name)
            self.exit_action()
        self.current_state = None
        logger.debug('leaving %s', self.name)

    def set_init_state(self, init_state):
        """ Set the initial substate.
        Should the state contain substates define the
        initial one that is entered on parent state entry.
        """
        assert init_state.parent is self
        self.init_state = init_state

    def on_timeout(self, timeout_ms):
        """ Define the timeout [ms].
        Return the state transition.
        """
        self.timer = Timer(timeout_ms,
                           lambda : self.send_signal(self.timeout),
                           Timer.SINGLE_SHOT)
        self.transitions[self.timeout] = Transition(self)
        return self.transitions[self.timeout]

    def send_signal(self, signal):
        """ Try to handle the given signal.
        Check if state cares about the signal. Exit
        the state and its substates and parents if jumping up in
        the hierarchy. Do the transition. Enter target state and
        its parents if they are not in active branch.
        """
        for sig, transition in self.transitions.items():
            if signal == sig:
                logger.debug('signal %s in state %s', signal.name, self.name)
                target = transition.target
                # Transition condition
                if transition.condition is not None\
                   and not transition.condition():
                    return False

                common_parent = _find_common_parent(self, target)

                # Exit
                common_parent.current_state.exit()

                # Transition
                if transition.action:
                    transition.action()

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
        return False

class Signal(): # pylint: disable=too-few-public-methods
    """ State machine signal.
    Send the signal to the state to do some actions
    and to jump to another state.
    """
    def __init__(self, name='noname'):
        self.name = name

class StateMachine(State):
    """ Finite state machine.
    Super state that wraps the entired hierarchical state
    machine. Send signal to it to do anything.
    Signal is put on the stack. On process_signal a single
    signal from the stack is handled. Start the machine
    before trying to process a signal.
    """
    def __init__(self, name='StateMachine'):
        super().__init__(name)
        self.signal_stack = []

    def start(self):
        """ Start the machine.
        Do all initial transitions.
        """
        assert self.init_state
        super().start()

    def send_signal(self, signal):
        """ Put a signal on a stack.
        Call process_signal to dequeue the oldest
        signal and handle it (do transition, perform action, ...).
        """
        self.signal_stack.append(signal)

    def process_signal(self):
        """ Handle single signal in queue.
        Process the oldest signal from queue.
        Go through active state machine branch, try find the state
        that accepts the given signal.
        """
        if self.anything_to_do():
            signal = self.signal_stack.pop(0)
            state = self.current_state
            while state is not None:
                if state.send_signal(signal):
                    return True
                state = state.current_state
        return False

    def anything_to_do(self):
        """ Return True if any signals are left
        on the signal stack."""
        return len(self.signal_stack) > 0

class Choice(State):
    """ State choice.
    A wrapper state to mimic a conditional state transition.
    """
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.entered = []

    def go_to_if(self, target, condition):
        """ Define the conditional state transition.
        Return the conditional state transition. A transition
        to the target is done only if condition evaluates to True.
        """
        self.entered.append(Signal(f'entered #{len(self.entered)}'))
        return self.on_signal(self.entered[-1]).go_to(target, condition)

    def enter(self):
        """ Enter th state."""
        super().enter()
        for s in self.entered:
            self.send_signal(s)
