import unittest
from unittest.mock import patch

class DcMotorDriveTest(unittest.TestCase):
    def test_pin_config(self):
        with patch('builtins.__import__'):
            from coop_door import dcmotor_drive
        #motor = dcmotor_drive.Motor(6, 2)
        #mock_machine.Pin.OUT = 1
        #mock_machine.Pin.called_with(6, mock_machine.Pin.OUT)
        #mock_machine.Pin.called_with(2, mock_machine.Pin.OUT)

if __name__ == '__main__':
	unittest.main()