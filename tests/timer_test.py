import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import sys
sys.modules['machine.timer'] = MagicMock()
from ..coop_door.timer import Timer

@pytest.fixture
def machine_timer_mock():
    return MagicMock()

@pytest.fixture
def slot():
    return lambda:False

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
        calls = [call()]
        MachineTimer_mock.assert_has_calls(calls)

def test_start(timer, machine_timer_mock, timeout, slot):
    timer.start()
    calls = [call(period=timeout, callback=slot)]
    machine_timer_mock.init.assert_has_calls(calls)

def test_stop(timer, machine_timer_mock):
    timer.stop()
    calls = [call()]
    machine_timer_mock.deinit.assert_has_calls(calls)
