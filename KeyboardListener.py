import logging
from pynput import keyboard
from random import randint

from avl_can import CANClient
from obd_listener import OBDTracker


class KeyboardListener:
    def __init__(self, client: CANClient or OBDTracker):
        self.client = client
        self.keyboard_listener = None

    def on_press(self, key: keyboard.Key):
        try:
            if key.char == 's' or key.char == 'S':
                data = [randint(0, 15) for i in range(randint(0, 8))]
                logging.info(
                    "Generated random CAN message with data: {}".format(data))
                self.client.send_message(arb_id=100, data=data)
            elif key.char == 'p' or key.char == 'P':
                logging.info("Pausing the listener...")
                self.client.stop_listener()
            elif key.char == 'c' or key.char == 'C':
                logging.info("Restarting the async listener...")
                self.client.listen_async()
            elif key.char == 'r' or key.char == 'R':
                logging.info("Reconnecting...")
                self.client.shutdown()
                self.client.connect()
        except AttributeError:
            pass
        finally:
            pass

    def on_release(self, key: keyboard.Key):
        if key == keyboard.Key.esc:
            logging.info("Exiting...")
            self.keyboard_listener.stop()
            return False

    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as key_listener:
            self.keyboard_listener = key_listener
            logging.info("Keyboard listener is activated.")
            key_listener.join()
            self.client.shutdown()
