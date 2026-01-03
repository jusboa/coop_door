import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.timer import Timer

@pytest.fixture
def machine_timer_mock():
    m = MagicMock()
    m.PERIODIC = 321
    m.ONE_SHOT = 567
    return MagicMock()

@pytest.fixture
def slot():
    return MagicMock()

@pytest.fixture
def timeout():
    return 444

@pytest.fixture
def timer(machine_timer_mock, timeout, slot):
    with patch('coop_door.coop_door.timer.MachineTimer') as MachineTimer_mock:
        MachineTimer_mock.return_value = machine_timer_mock
        return Timer(timeout, slot)

def test_machine_timer_creation(timeout, slot):
    with patch('coop_door.coop_door.timer.MachineTimer') as MachineTimer_mock:
        Timer(timeout, slot)
        MachineTimer_mock.assert_called_once()

def test_start(timer, machine_timer_mock, timeout, slot):
    timer.start()
    machine_timer_mock.init.assert_called_once()
    assert machine_timer_mock.init.call_args.kwargs['mode'] == machine_timer_mock.PERIODIC
    assert machine_timer_mock.init.call_args.kwargs['period'] == timeout
    machine_timer_mock.init.call_args.kwargs['callback'](None)
    slot.assert_called_once()

def test_single_shot(machine_timer_mock):
    with patch('coop_door.coop_door.timer.MachineTimer') as MachineTimer_mock:
        MachineTimer_mock.return_value = machine_timer_mock
        timer = Timer(timeout, slot, Timer.SINGLE_SHOT)
        timer.start()
        machine_timer_mock.init.assert_called_once()
        assert machine_timer_mock.init.call_args.kwargs['mode'] == machine_timer_mock.ONE_SHOT

def test_stop(timer, machine_timer_mock):
    timer.stop()
    machine_timer_mock.deinit.assert_called_once()

def test_active_while_running(timer):
    timer.start()
    assert timer.active()
    timer.stop()
    assert not timer.active()

def test_becomes_inactive_after_timeout(timer, machine_timer_mock):
    timer.start()
    machine_timer_slot = machine_timer_mock.init.call_args.kwargs['callback']
    machine_timer_slot(None)
    assert not timer.active()

del sys.modules['machine']
