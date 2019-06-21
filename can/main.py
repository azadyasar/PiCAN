from CANListener import CANListener
from config import Config
import sys
import can
import logging
from pynput import keyboard

logging.getLogger().setLevel(logging.INFO)


class KeyboardListener:
    def __init__(self, can_listener):
        self.can_listener = can_listener

    def on_press(self, key: keyboard.Key):
        try:
            print('Alphanumeric key {0} pressed'.format(key.char))
            if key.char == 's':
                logging.info("Sending a random can message")
                self.can_listener.send_message(
                    arb_id=100, data=[1, 2, 3, 4, 5, 6])
        except AttributeError:
            print('Special key {0} pressed'.format(key))

    def on_release(self, key: keyboard.Key):
        if key == keyboard.Key.esc:
            # Stop listener
            return False

    def start_keyboard(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as key_listener:
            key_listener.join()
            self.can_listener.bus.shutdown()
            self.can_listener.can_listener_thread._stop()


if __name__ == "__main__":

    config = Config()
    config_dict = config.read_config()
    logging.info("Config dict is read: {}".format(config_dict))

    bustype, channel, bitrate = config_dict[config.NETWORK_STR][config.BUSTYPE_STR], config_dict[config.NETWORK_STR][
        config.CHANNEL_STR], config_dict[config.NETWORK_STR][config.BITRATE_STR]
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
    # can_listener.listen_asynchronously()
    can_listener_thread = can_listener.start_background_listener()
    keyboard_listener = KeyboardListener(can_listener)
    keyboard_listener.start_keyboard()
    can_listener_thread.join()
    logging.info("Stopped listening. Cleaning up..")
