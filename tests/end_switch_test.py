import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door.end_switch import EndSwitch

@pytest.fixture
def pin_mock():
    return MagicMock()

@pytest.fixture
def observer_mock():
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
        Pin_mock.assert_called_once_with(11, 88, 44)

def test_switch_state(pin_mock, switch):
    pin_mock.value.return_value = False
    assert switch.is_on()
    pin_mock.value.return_value = True
    assert not switch.is_on()

def test_slot_is_called_on_state_change(switch,
                                        observer_mock,
                                        pin_mock):
    switch.register_slot(observer_mock)
    pin_mock.value.return_value = False
    switch.read()
    pin_mock.value.return_value = True
    switch.read()
    observer_mock.assert_called_with(False)
    pin_mock.value.return_value = False
    switch.read()
    observer_mock.assert_called_with(True)
    
del sys.modules['machine']
