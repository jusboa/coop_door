import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.state_machine import StateMachine, State, Signal, Choice

sys.modules['coop_door.coop_door.timer'] = MagicMock()

@pytest.fixture
def timer_mock():
    return MagicMock()

@pytest.fixture
def state_machine():
    return StateMachine()

@pytest.fixture
def states(state_machine):
    states = {'red' : State('red', state_machine),
              'green' : State('green', state_machine),
              'orange' : State('orange', state_machine)}
    return states

def send_signal(state_machine, signal):
    state_machine.send_signal(signal)
    state_machine.process_signal()

def test_state_has_name(states):
    assert states['red'].name == 'red'
    states['red'].name = 'black'
    assert states['red'].name == 'black'

def test_set_init_state(state_machine, states):
    # This works.
    state_machine.set_init_state(states['orange'])
    # This fails.
    blue = State('blue')
    with pytest.raises(AssertionError):
        state_machine.set_init_state(blue)

def test_start_without_init_state(state_machine):
    with pytest.raises(AssertionError):
        state_machine.start()

def test_current_state_on_init(state_machine, states):
    state_machine.set_init_state(states['green'])
    assert state_machine.current_state is None

def test_current_state_after_start(state_machine, states):
    state_machine.set_init_state(states['green'])
    state_machine.start()
    assert state_machine.current_state is states['green']

def test_state_transtion(state_machine, states):
    go = Signal()
    states['red'].on_signal(go).go_to(states['orange'])
    state_machine.set_init_state(states['red'])
    state_machine.start()
    send_signal(state_machine, go)
    assert state_machine.current_state is states['orange']

def test_irrelevant_signals_are_ignored(state_machine, states):
    go = Signal()
    stop = Signal()
    states['red'].on_signal(go).go_to(states['green'])
    states['green'].on_signal(go).go_to(states['red'])
    state_machine.set_init_state(states['red'])
    state_machine.start()
    send_signal(state_machine, stop)
    assert state_machine.current_state is states['red']
    
def test_transition_action(state_machine, states):
    go = Signal()
    actions = []
    states['red'].on_signal(go).do(lambda x=actions:x.append('red')).go_to(states['green'])
    state_machine.set_init_state(states['red'])
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['red']

def test_entry_action(state_machine, states):
    go = Signal()
    actions = []
    states['red'].do_on_entry(lambda x=actions:x.append('red')).on_signal(go).go_to(states['green'])
    state_machine.set_init_state(states['red'])
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['red']

def test_init_state_entry_action_on_start(state_machine, states):
    actions = []
    states['red'].do_on_entry(lambda x=actions:x.append('red'))
    state_machine.set_init_state(states['red'])
    state_machine.start()
    assert actions == ['red']

def test_exit_action(state_machine, states):
    go = Signal()
    actions = []
    states['red'].do_on_exit(lambda x=actions:x.append('red')).on_signal(go).go_to(states['green'])
    state_machine.set_init_state(states['red'])
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['red']

def test_current_state_of_nested_states(state_machine, states):
    another_state = State('another_state', states['red'])
    states['red'].set_init_state(another_state)
    state_machine.set_init_state(states['red'])
    state_machine.start()
    assert state_machine.current_state is states['red']

def test_entry_actions_of_nested_states_on_start(state_machine, states):
    actions = []
    state_machine.set_init_state(states['red'])
    states['red'].do_on_entry(lambda x=actions:x.append('red'))
    inner_state = State('inner_state', states['red'])
    inner_state.do_on_entry(lambda x=actions:x.append('inner_state'))
    states['red'].set_init_state(inner_state)
    inner_inner_state = State('inner_inner_state', inner_state)
    inner_state.set_init_state(inner_inner_state)
    inner_inner_state.do_on_entry(lambda x=actions:x.append('inner_inner_state'))
    state_machine.start()
    assert actions == ['red', 'inner_state', 'inner_inner_state']

def test_entry_actions_of_nested_states_on_signal(state_machine, states):
    actions = []
    state_machine.set_init_state(states['red'])
    go = Signal()
    states['red'].on_signal(go).go_to(states['green'])
    states['green'].do_on_entry(lambda x=actions:x.append('green'))
    inner_state = State('inner_state', states['green'])
    inner_state.do_on_entry(lambda x=actions:x.append('inner_state'))
    states['green'].set_init_state(inner_state)
    inner_inner_state = State('inner_inner_state', inner_state)
    inner_state.set_init_state(inner_inner_state)
    inner_inner_state.do_on_entry(lambda x=actions:x.append('inner_inner_state'))
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['green', 'inner_state', 'inner_inner_state']

def test_exit_actions_of_nested_states(state_machine, states):
    actions = []
    state_machine.set_init_state(states['red'])
    go = Signal()
    states['red'].on_signal(go).go_to(states['green'])
    states['red'].do_on_exit(lambda x=actions:x.append('red'))
    inner_state = State('inner_state', states['red'])
    inner_state.do_on_exit(lambda x=actions:x.append('inner_state'))
    states['red'].set_init_state(inner_state)
    inner_inner_state = State('inner_inner_state', inner_state)
    inner_state.set_init_state(inner_inner_state)
    inner_inner_state.do_on_exit(lambda x=actions:x.append('inner_inner_state'))
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['inner_inner_state', 'inner_state', 'red']

def test_simple_state_machine(state_machine, states):
    actions = []
    idle = State('idle', state_machine)
    active = State('active', state_machine)
    states['red'] = State('red', active)
    states['green'] = State('green', active)
    states['orange'] = State('orange', active)
    active.set_init_state(states['red'])
    state_machine.set_init_state(idle)
    go_delay_expired = Signal()
    stop_delay_expired = Signal()
    go = Signal()
    stop = Signal()
    wakeup = Signal()
    sleep = Signal()
    idle.on_signal(wakeup).go_to(active)
    active.on_signal(sleep).go_to(idle)
    states['red'].on_signal(go).go_to(states['orange'])
    states['orange'].on_signal(go_delay_expired).go_to(states['green'])
    states['orange'].on_signal(stop_delay_expired).go_to(states['red'])
    states['green'].on_signal(stop).go_to(states['orange'])
    idle.do_on_entry(lambda x=actions:x.append('idle'))
    active.do_on_entry(lambda x=actions:x.append('active'))
    states['red'].do_on_entry(lambda x=actions:x.append('red'))
    states['green'].do_on_entry(lambda x=actions:x.append('green'))
    states['orange'].do_on_entry(lambda x=actions:x.append('orange'))
    state_machine.start()
    send_signal(state_machine, wakeup)
    send_signal(state_machine, go)
    send_signal(state_machine, go_delay_expired)
    send_signal(state_machine, stop)
    send_signal(state_machine, stop_delay_expired)
    send_signal(state_machine, sleep)
    assert actions == ['idle', 'active', 'red', 'orange', 'green', 'orange', 'red', 'idle']

def test_direct_transition_from_child_state(state_machine, states):
    actions = []
    go = Signal()
    singleton = State('singleton', state_machine)
    super_state = State('super_state', state_machine)
    child_state = State('child_state', super_state)
    child_state.on_signal(go).go_to(singleton)
    state_machine.set_init_state(super_state)
    super_state.set_init_state(child_state)
    super_state.do_on_exit(lambda x=actions:x.append('super_state'))
    child_state.do_on_exit(lambda x=actions:x.append('child_state'))
    singleton.do_on_entry(lambda x=actions:x.append('singleton'))
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['child_state', 'super_state', 'singleton']
    assert state_machine.current_state == singleton

def test_direct_transition_to_child_state(state_machine, states):
    actions = []
    go = Signal()
    singleton = State('singleton', state_machine)
    super_state = State('super_state', state_machine)
    child_state = State('child_state', super_state)
    singleton.on_signal(go).go_to(child_state)
    state_machine.set_init_state(singleton)
    super_state.set_init_state(child_state)
    super_state.do_on_entry(lambda x=actions:x.append('super_state'))
    child_state.do_on_entry(lambda x=actions:x.append('child_state'))
    state_machine.start()
    send_signal(state_machine, go)
    assert actions == ['super_state', 'child_state']
    
def test_time_limited_state_creates_timer(state_machine, states):
    calls = []
    timeout_slot = None
    with patch('coop_door.coop_door.state_machine.Timer') as Timer_mock:
        timeout_expct = 300
        Timer_mock.SINGLE_SHOT = 999
        states['orange'].do_on_entry(lambda x=calls : calls.append('orange')).on_timeout(timeout_expct).go_to(states['green'])
        Timer_mock.assert_called_once()
        assert Timer_mock.call_args.args[0] == timeout_expct
        assert Timer_mock.call_args.args[2] == Timer_mock.SINGLE_SHOT
        timeout_slot = Timer_mock.call_args.args[1]
        states['green'].do_on_entry(lambda x=calls : calls.append('green'))
        state_machine.set_init_state(states['orange'])
        state_machine.start()
        timeout_slot()
        assert calls == ['orange', 'green']

def test_timer_starts_on_entry(state_machine, states, timer_mock):
    with patch('coop_door.coop_door.state_machine.Timer') as Timer_mock:
        Timer_mock.return_value = timer_mock
        go = Signal()
        states['red'].on_signal(go).go_to(states['orange'])
        states['orange'].on_timeout(100).go_to(states['green'])
        state_machine.set_init_state(states['red'])
        state_machine.start()
        send_signal(state_machine, go)
        timer_mock.start.assert_called_once()


def test_timer_stops_on_exit(state_machine, states, timer_mock):
    with patch('coop_door.coop_door.state_machine.Timer') as Timer_mock:
        Timer_mock.return_value = timer_mock
        go = Signal()
        states['red'].on_signal(go).go_to(states['orange'])
        states['orange'].on_timeout(100).go_to(states['green'])
        callback = Timer_mock.call_args.args[1]
        state_machine.set_init_state(states['red'])
        state_machine.start()
        send_signal(state_machine, go)
        callback()
        timer_mock.stop.assert_called_once()

def test_choice(state_machine, states):
    calls = []
    is_lane_stopped = Choice('is_lane_stopped', state_machine)
    is_fast_lights = Choice('is_fast_lights', state_machine)
    is_lane_stopped.do_on_entry(lambda x=calls : calls.append('is_lane_stopped'))
    states['green'].do_on_entry(lambda x=calls : calls.append('green'))
    states['red'].do_on_entry(lambda x=calls : calls.append('red'))
    states['orange'].do_on_entry(lambda x=calls : calls.append('orange'))
    state_machine.set_init_state(is_lane_stopped)
    is_lane_stopped.go_to_if(states['red'], lambda:False)
    is_lane_stopped.go_to_if(is_fast_lights, lambda:True)
    is_fast_lights.go_to_if(states['green'], lambda:True)
    is_fast_lights.go_to_if(states['orange'], lambda:False)
    state_machine.start()
    assert calls == ['is_lane_stopped', 'green']

def test_choice_actions_are_executed(state_machine, states):
    calls = []
    is_lane_stopped = Choice('is_lane_stopped', state_machine)
    is_fast_lights = Choice('is_fast_lights', state_machine)
    state_machine.set_init_state(is_lane_stopped)
    is_lane_stopped.go_to_if(states['red'], lambda:False).do(lambda x=calls : calls.append('red action'))
    is_lane_stopped.go_to_if(is_fast_lights, lambda:True).do(lambda x=calls : calls.append('fast lights action'))
    is_fast_lights.go_to_if(states['green'], lambda:True).do(lambda x=calls : calls.append('green action'))
    is_fast_lights.go_to_if(states['orange'], lambda:False).do(lambda x=calls : calls.append('orange action'))
    state_machine.start()
    assert calls == ['fast lights action', 'green action']

del sys.modules['machine']
del sys.modules['coop_door.coop_door.timer']

