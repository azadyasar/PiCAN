import logging
# from pynput import keyboard
from random import randint

from avl_can import CANClient
from obd_listener import OBDTracker
from can.interfaces.pcan.pcan import PcanError

import keyboard


class KeyboardListener(object):
    def __init__(self, client: CANClient or OBDTracker, is_secured: bool = False):
        self.client = client
        self.is_secured = is_secured
        self.running_ = False

    def start(self):
        self.running_ = True
        while self.running_:
            req = input()
            if req == "q" or req == "Q":
                logging.info("Stopping keyboard listener")
                self.running_ = False
            elif req == "su" or req == "SU":
                self.client.searchUSB()

    def stop(self):
        self.running_ = False

# class KeyboardListener(object):
#     def __init__(self, client: CANClient or OBDTracker, is_secured: bool = False):
#         self.client = client
#         self.is_secured = is_secured

#         self.setup()

#     def on_press(self, key: keyboard.KeyboardEvent):
#         # print("Device: ", key.device)
#         # print("Event type: ", key.event_type)
#         # print("is_keypad: ", key.is_keypad)
#         # print(key, key.name)
#         if key.name == "esc":
#             print("esc pressed")

#     def send(self):
#         if self.is_secured:
#             data = [randint(0, 15) for i in range(randint(0, 8))]
#             id = randint(0, 255)
#             logging.info(
#                 "Generated random CAN message with params => A_ID: {}, data: {}".format(id, data))
#             self.client.send_message(arb_id=id, data=data)
#         else:
#             logging.info(
#                 "You're running in insecure mode. Run with -s flag to be able to send messages into the network.")

#     def restart(self):
#         try:
#             self.client.listen_async()
#         except PcanError as pcanErr:
#             logging.error(
#                 "Error occured while trying to listen to the CAN bus.\n\tDetails: {}".format(pcanErr))

#     def reconnect(self):
#         logging.info("Reconnecting...")
#         self.client.shutdown()
#         self.client.connect()

#     def setup(self):
#         print("Setting up keyboard")
#         self.key_press_callbacks = {'shift+w':
#                                     self.client.watch,
#                                     'shift+s': self.send,
#                                     'shift+q': self.client.stop_watcher,
#                                     'shift+p': self.client.stop_listener,
#                                     'shift+c': self.restart,
#                                     'shift+r': self.reconnect}
#         for key_comb in self.key_press_callbacks:
#             keyboard.add_hotkey(key_comb, self.key_press_callbacks[key_comb])
#         # keyboard.add_hotkey('page up, page down',
#         #                     lambda: print('foobar'))
#         # keyboard.add_hotkey('ctrl+shift+a', lambda: print('CSA'))

#     def start(self):
#         print("Starting keyboard listener...")
#         keyboard.on_press(self.on_press)
#         keyboard.wait("esc")
#         print("Shutting down...")


# class KeyboardListener:
#     def __init__(self, client: CANClient or OBDTracker, is_secured: bool = False):
#         self.client = client
#         self.keyboard_listener = None
#         self.is_secured = is_secured
#         self._is_shift_pressed = False
#         self._COMBINATIONS = [
#             {keyboard.Key.shift, keyboard.KeyCode(char='c')}
#         ]

#     def on_press(self, key: keyboard.Key):
#         if key == keyboard.Key.shift:
#             self._is_shift_pressed = True
#             return
#         try:
#             if (key.char == 's' or key.char == 'S') and self._is_shift_pressed:
#                 if self.is_secured:
#                     data = [randint(0, 15) for i in range(randint(0, 8))]
#                     id = randint(0, 255)
#                     logging.info(
#                         "Generated random CAN message with id: {} and data: {}".format(id, data))
#                     self.client.send_message(arb_id=id, data=data)
#                 else:
#                     logging.info(
#                         "You're running in insecure mode. Run with -s flag on to send messages into the network.")
#             elif (key.char == 'w' or key.char == 'W') and self._is_shift_pressed:
#                 self.client.watch()
#             elif (key.char == 'q' or key.char == 'Q') and self._is_shift_pressed:
#                 self.client.stop_watcher()
#             elif (key.char == 'p' or key.char == 'P') and self._is_shift_pressed:
#                 logging.info("Pausing the listener...")
#                 self.client.stop_listener()
#             elif (key.char == 'c' or key.char == 'C') and self._is_shift_pressed:
#                 logging.info("Restarting the async listener...")
#                 try:
#                     self.client.listen_async()
#                 except PcanError as pcanErr:
#                     logging.error(
#                         "Error occured while trying to listen to the CAN bus.\n\tDetais: {}".format(pcanErr))
#             elif (key.char == 'r' or key.char == 'R') and self._is_shift_pressed:
#                 logging.info("Reconnecting...")
#                 self.client.shutdown()
#                 self.client.connect()
#         except AttributeError:
#             pass
#         finally:
#             pass

#     def on_release(self, key: keyboard.Key):
#         if key == keyboard.Key.shift:
#             self._is_shift_pressed = False
#             return
#         if key == keyboard.Key.esc:
#             logging.info("Exiting...")
#             self.keyboard_listener.stop()
#             return False

#     def start(self):
#         with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as key_listener:
#             self.keyboard_listener = key_listener
#             logging.info("Keyboard listener is activated.")
#             try:
#                 key_listener.join()
#             except KeyboardInterrupt as interrupt:
#                 logging.info("Keyboard interrupt received. Hit ESC to exit.")
#             self.client.shutdown()
