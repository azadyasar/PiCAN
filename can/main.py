from CANListener import CANListener
from config import Config
import sys
import can
import logging

from can_constants import CAN_CONSTANTS
from KeyboardListener import KeyboardListener

logging.getLogger().setLevel(logging.INFO)


if __name__ == "__main__":

    config = Config()
    config_dict = config.read_config()
    logging.info("Config dict is read: {}".format(config_dict))

    bustype, channel, bitrate = config_dict[CAN_CONSTANTS.NETWORK_STR][CAN_CONSTANTS.BUSTYPE_STR], config_dict[CAN_CONSTANTS.NETWORK_STR][
        CAN_CONSTANTS.CHANNEL_STR], config_dict[CAN_CONSTANTS.NETWORK_STR][CAN_CONSTANTS.BITRATE_STR]
    bus = None
    try:
        bus = can.interface.Bus(
            channel=channel, bustype=bustype, bitrate=bitrate)
    except OSError as osError:
        logging.error(
            "Error while connecting to the CAN bus.\nDetails: {}".format(osError))
        logging.error("Terminating...")
        sys.exit(1)

    can_listener = CANListener(bus, config_dict)
    logging.info("Starting async listener")
    can_listener.start_background_listener()
    keyboard_listener = KeyboardListener(can_listener)
    keyboard_listener.start()
    if bus is not None:
        bus.shutdown()
    logging.info("Stopped listening. Cleaning up..")
