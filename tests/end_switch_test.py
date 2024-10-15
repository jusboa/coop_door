import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.end_switch import EndSwitch

@pytest.fixture
def pin_mock():
    return MagicMock()

@pytest.fixture
def switch(pin_mock):
    with patch('coop_door.coop_door.end_switch.Pin') as Pin_mock:
        Pin_mock.return_value = pin_mock
        return EndSwitch(3)

def test_pin_config():
    with patch('coop_door.coop_door.end_switch.Pin') as Pin_mock:
        Pin_mock.IN = 88
        Pin_mock.PULL_UP = 44
        EndSwitch(11)
        calls = [call(11, 88, 44)]
        Pin_mock.assert_has_calls(calls)

def test_switchState(pin_mock, switch):
    pin_mock.value.return_value = False
    assert switch.is_on()
    pin_mock.value.return_value = True
    assert not switch.is_on()
