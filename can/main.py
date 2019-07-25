from CANListener import CANListener
from config import Config
import sys
import can
import logging
from pynput import keyboard
from random import randint

from can_constants import CAN_CONSTANTS

logging.getLogger().setLevel(logging.INFO)


class KeyboardListener:
    def __init__(self, can_listener):
        self.can_listener = can_listener
        self.keyboard_listener = None

    def on_press(self, key: keyboard.Key):
        try:
            # print('Alphanumeric key {0} pressed'.format(key.char))
            if key.char == 's':
                data = [randint(0, 15) for i in range(randint(0, 8))]
                logging.info(
                    "Sending a random can message with data: {}".format(data))
                self.can_listener.send_message(
                    arb_id=100, data=data)
            elif key.char == 'p' or key.char == 'P':
                logging.info("Pausing the listener")
                self.can_listener.stop_async_listener()
            elif key.char == 'c' or key.char == 'C':
                logging.info("Restarting the async listener")
                self.can_listener.start_background_listener()
        except AttributeError:
            # print('Special key {0} pressed'.format(key))
            pass

    def on_release(self, key: keyboard.Key):
        if key == keyboard.Key.esc:
            # Stop listener
            logging.info("Exiting...")
            self.keyboard_listener.stop()
            return False

    def start(self):
        logging.info("Keyboard listener is being activated.")
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as key_listener:
            self.keyboard_listener = key_listener
            key_listener.join()
            if self.can_listener.notifier is not None:
                self.can_listener.stop_async_listener()


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
            "Error while trying to initialize the CAN bus.\nDetails: {}".format(osError))
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
