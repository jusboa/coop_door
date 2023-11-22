import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import call

import sys
sys.modules['machine'] = MagicMock()
from ..coop_door import dcmotor_drive

class DcMotorDriveTest(unittest.TestCase):
    def setUp(self):
        with patch('coop_door.coop_door.dcmotor_drive.Pin') as Pin_mock:
            self.pin0_mock = MagicMock()
            self.pin1_mock = MagicMock()
            Pin_mock.side_effect = [self.pin0_mock, self.pin1_mock]
            self.motor = dcmotor_drive.Motor(0, 1)

    def test_pin_config(self):
        with patch('coop_door.coop_door.dcmotor_drive.Pin') as Pin_mock:
            Pin_mock.OUT = 33
            dcmotor_drive.Motor(0, 1)
            calls = [call(0, 33), call(1, 33)]
            Pin_mock.assert_has_calls(calls)

    def test_forward(self):
        self.motor.forward()
        self.pin0_mock.value.assert_called_once_with(1)
        self.pin1_mock.value.assert_called_once_with(0)
    
    def test_backward(self):
        self.motor.backward()
        self.pin0_mock.value.assert_called_once_with(0)
        self.pin1_mock.value.assert_called_once_with(1)

if __name__ == '__main__':
	unittest.main()