import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door import end_switch

class TestEndSwitch(unittest.TestCase):
    def setUp(self):
        with patch('coop_door.coop_door.end_switch.Pin') as Pin_mock:
            self.pin_mock = MagicMock()
            Pin_mock.side_effect = [self.pin_mock]
            self.PIN_NUMBER = 3
            self.end_switch = end_switch.EndSwitch(self.PIN_NUMBER)

    def test_pin_config(self):
        with patch('coop_door.coop_door.end_switch.Pin') as Pin_mock:
            Pin_mock.IN = 88
            Pin_mock.PULL_UP = 44
            end_switch.EndSwitch(11)
            calls = [call(11, 88, 44)]
            Pin_mock.assert_has_calls(calls)

    def test_switchState(self):
        self.pin_mock.value.return_value = False
        self.assertTrue(self.end_switch.isOn())
        self.pin_mock.value.return_value = True
        self.assertFalse(self.end_switch.isOn())
