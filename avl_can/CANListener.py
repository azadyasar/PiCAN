import can
from can.bus import BusState
import asyncio
import signal

from threading import Thread
import threading

try:
    from .CANMessage import CANMessage
except ImportError:
    from CANMessage import CANMessage

try:
    from .can_constants import CAN_CONSTANTS
except ImportError:
    from can_constants import CAN_CONSTANTS

import logging
import inspect
logging.getLogger().setLevel(logging.INFO)


class CANListener:
    def __init__(self, bus, config={}):
        self.bus = bus
        self.config = config
        self.listener_thread = None
        self.notifier = None
        self.loop = None
        self.listener_thread = None
        self.construct_id_desc_mapping()
        self.init_can_messages()
        self.construct_message_id_mapping()

    def construct_id_desc_mapping(self):
        # Stores the CAN message IDs (retrieved from the config.yaml file)
        # and their corresponding descriptions. e.g., {1: 'eng_speed'}
        self.msg_id_desc_map = {}  # set()
        if self.config is not None and CAN_CONSTANTS.CAN_MESSAGES_STR in self.config:
            for can_msg in self.config[CAN_CONSTANTS.CAN_MESSAGES_STR]:
                logging.info("Reading {} message information".format(can_msg))
                id = can_msg[CAN_CONSTANTS.ID_STR]
                self.msg_id_desc_map[id] = can_msg[CAN_CONSTANTS.DESC_STR]
            logging.info("Constructed requested CAN Message ID - Description Table. # of Entries: {}".format(
                len(self.msg_id_desc_map)))
        elif self.config is not None and CAN_CONSTANTS.CAN_MESSAGES_STR not in self.config:
            logging.warning("config does not include {0}".format(
                CAN_CONSTANTS.CAN_MESSAGES_STR))

    def init_can_messages(self):
        # Stores the latest CAN messages as CAN_Message_ID - CANMessage pairs
        self.can_data = {}
        for can_msg_id in self.msg_id_desc_map:
            self.can_data[can_msg_id] = CANMessage(
                id=can_msg_id, desc=self.msg_id_desc_map[can_msg_id])

    def construct_message_id_mapping(self):
        logging.debug("Constructing self.desc_id_dict")
        if self.msg_id_desc_map is None:
            func_info = inspect.currentframe().f_back.f_code
            logging.warning(
                "[{}]: Must initialize self.msg_id_desc_map first".format(func_info.co_name))
        # Construct description-id map
        self.desc_id_dict = {}
        for can_msg_id in self.msg_id_desc_map:
            self.desc_id_dict[self.msg_id_desc_map[can_msg_id]] = can_msg_id

    def set_bus(self, bus):
        self.bus = bus

    def get_bus(self):
        return self.bus

    def print_config_msgs(self):
        for index, msg_id in enumerate(self.msg_id_desc_map):
            print("{}: ID: {} # Description: {}".format(
                index, msg_id, self.msg_id_desc_map[msg_id]))

    def receive_all(self):
        try:
            print("Started listening to all CAN messages. Hit CTRL+C to stop")
            while True:
                msg = self.bus.recv(1)  # 1 sec timeout
                if msg is not None:
                    print(msg)
        except KeyboardInterrupt:
            print("KeyboardInterrupt! Stopped listening to the CAN bus")
            pass

    '''
    Filters out the CAN messages that are not in the config.yaml file.
    '''

    def receive_config_msgs(self):
        try:
            print("Started listening to the requested CAN messages. Hit CTRL+C to stop")
            print("Requested CAN message IDs: {}".format(self.msg_id_desc_map))
            while True:
                msg = self.bus.recv(1)
                if msg is not None and msg.arbitration_id in self.msg_id_desc_map:
                    print(msg)
                elif msg is not None:
                    print(
                        "[DEBUG] Message is not in the requested messages:\n{}".format(msg))
        except KeyboardInterrupt:
            print("keyboardInterrupt! Stopped listening to the CAN bus")
            pass

    def start_background_listener(self) -> Thread:
        if (self.listener_thread is not None and self.listener_thread.is_alive()):
            logging.info("A thread is already running. Shutting it down..")
            self.stop_async_listener()
        self.listener_thread = Thread(target=self.listen_asynchronously)
        self.listener_thread.start()
        return self.listener_thread
        # try:
        #     thread.join()
        # except KeyboardInterrupt:
        #     logging.info("Keyboard interrupt. Stopping...")

    def listen_asynchronously(self):
        func_info = inspect.currentframe().f_back.f_code
        if self.bus is None:
            logging.warning(
                "[{}]: Must set bus first".format(func_info.co_name))
            return
        listeners = [self.listen_async_cb]
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        logging.info("Starting the notifier loop...")
        self.notifier = can.Notifier(self.bus, listeners, loop=self.loop)
        if not self.loop.is_running():
            self.loop.run_forever()

    def stop_async_listener(self):
        if self.notifier is not None:
            logging.info("Shutting down the background loop..")
            self.notifier.stop()
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.listener_thread.join()
            self.loop = None
            self.notifier = None
            self.listener_thread = None
        else:
            logging.info("No listeners are running...")

    def listen_async_cb(self, msg):
        print(msg)
        CANListener.print_postproc()

    def send_message(self, arb_id, data):
        can_message = can.Message(arbitration_id=arb_id, data=data)
        try:
            self.bus.send(can_message)
        except can.CanError as canErr:
            logging.error(
                "Error while sending a CAN message {}".format(canErr))

    @staticmethod
    def print_postproc():
        print("Finished processing.")

    @staticmethod
    def addon_can_cb(msg):
        print("Addon CAN callback: {}".format(msg))
