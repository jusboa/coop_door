from coop_door.door_controller import DoorController
import logging
import sys

root_logger = logging.getLogger()
formatter = logging.Formatter('[%(levelname)s]\t(+%(msecs)s) %(name)s %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
root_logger.addHandler(console_handler)

file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

root_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    c = DoorController()
    logger.info('----------- Starting the application -----------')
    c.start()
