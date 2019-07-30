import logging
from pynput import keyboard
from random import randint


class CANKeyboardListener:
    def __init__(self, can_listener):
        self.can_listener = can_listener
        self.keyboard_listener = None

    def on_press(self, key: keyboard.Key):
        try:
            # print('Alphanumeric key {0} pressed'.format(key.char))
            if key.char == 's' or key.char == 'S':
                data = [randint(0, 15) for i in range(randint(0, 8))]
                logging.info(
                    "Sending a random can message with data: {}".format(data))
                self.can_listener.send_message(
                    arb_id=100, data=data)
            elif key.char == 'p' or key.char == 'P':
                logging.info("Pausing the listener...")
                self.can_listener.stop_async_listener()
            elif key.char == 'c' or key.char == 'C':
                logging.info("Restarting the async listener...")
                self.can_listener.start_background_listener()
        except AttributeError:
            # print('Special key {0} pressed'.format(key))
            pass
        finally:
            pass

    def on_release(self, key: keyboard.Key):
        if key == keyboard.Key.esc:
            # Stop listener
            logging.info("Exiting...")
            self.keyboard_listener.stop()
            return False

    def start(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as key_listener:
            self.keyboard_listener = key_listener
            logging.info("Keyboard listener is activated.")
            key_listener.join()
            self.can_listener.stop_async_listener()
