from coop_door.door_controller import DoorController
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    c = DoorController()
    logger.info('----------- Starting the application -----------')
    c.start()
