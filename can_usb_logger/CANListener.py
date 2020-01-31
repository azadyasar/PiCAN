import can
from can.bus import BusState
import asyncio
import signal
import time
from threading import Thread, Lock
import threading

from .usb_writer import USBWriter

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
        self.logging_ = False
        self.logger_thread = None
        self.saver_thread = None
        self.listener_thread = None
        self.watcher_thread = None
        self.watcher_loop = None
        self.watcher_notifier = None
        self._watcher_start_time = None
        self.watched_msg_counter = 0
        self.usbWriter = USBWriter()
        self.can_batch_data_lock = Lock()
        self.can_batch_data = []
        self.can_id_data_map = {}
        self.csv_header = []
        self.init_can_ids()

    def init_can_ids(self):
        self.can_messages = {}
        if self.config is not None and CAN_CONSTANTS.CAN_MESSAGES_STR in self.config:
            for can_id in self.config[CAN_CONSTANTS.CAN_MESSAGES_STR]:
                self.can_messages[can_id] = -1
            logging.info("Watching CAN messages: {}".format(
                self.can_messages.keys()))
            csv_header = []
            csv_header.append("timestamp")
            for index, can_id in enumerate(self.can_messages):
                self.can_id_data_map[can_id] = index + 1
                csv_header.append(can_id)
            self.csv_header.append(csv_header)
            logging.info("Read {} of CAN message requests.".format(
                len(self.can_messages)))
        elif CAN_CONSTANTS.CAN_MESSAGES_STR not in self.config:
            logging.warning("CAN Config does not include {0}".format(
                CAN_CONSTANTS.CAN_MESSAGES_STR))

    def set_bus(self, bus):
        if self.listener_thread is not None:
            self.stop_async_listener()
        self.bus = bus

    def get_bus(self):
        return self.bus

    def searchUSB(self):
        self.usbWriter = USBWriter()

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
            print("Requested CAN message IDs: {}".format(
                self.can_messages.keys()))
            while True:
                msg = self.bus.recv(1)
                if msg is not None and msg.arbitration_id in self.can_messages.keys():
                    print(msg)
                elif msg is not None:
                    print(
                        "[DEBUG] Message is not in the requested messages:\n{}".format(msg))
        except KeyboardInterrupt:
            print("keyboardInterrupt! Stopped listening to the CAN bus")
            pass

    def start_logger(self) -> Thread:
        if (self.listener_thread is not None and self.listener_thread.is_alive()):
            logging.info(
                "A listener thread is already running. Shutting it down..")
            self.stop_async_listener()
        self.usbWriter.writeLine(self.csv_header)
        self.logging_ = True
        self.logger_thread = Thread(target=self.log)
        self.saver_thread = Thread(target=self.save)
        self.listener_thread = Thread(target=self.listen_asynchronously)
        self.listener_thread.start()
        logging.info("Starting the logger thread...")
        self.logger_thread.start()
        logging.info("Starting the saver thread...")
        self.saver_thread.start()
        return self.listener_thread
        # try:
        #     thread.join()
        # except KeyboardInterrupt:
        #     logging.info("Keyboard interrupt. Stopping...")

    def log(self):
        if not self.logging_:
            logging.info("CANListener is not logging anymore.")
            return
        can_data = [None] * (len(self.can_messages) + 1)
        can_data[0] = time.time()
        for can_id in self.can_messages:
            can_data[self.can_id_data_map[can_id]] = self.can_messages[can_id]
        self.can_batch_data_lock.acquire()
        logging.info("Logging [{}]".format(can_data))
        self.can_batch_data.append(can_data)
        self.can_batch_data_lock.release()
        thr = threading.Timer(1, self.log)
        thr.setDaemon(True)
        thr.start()

    def save(self):
        if not self.logging_:
            logging.info("CANListener is not logging anymore.")
            return
        self.can_batch_data_lock.acquire()
        if len(self.can_batch_data) is 0:
            self.can_batch_data_lock.release()
            logging.info("No batch can data to save..")
            return
        logging.info("Saving [{}]".format(self.can_batch_data))
        self.usbWriter.writeLine(self.can_batch_data)
        self.can_batch_data.clear()
        self.can_batch_data_lock.release()
        thr = threading.Timer(10, self.save)
        thr.setDaemon(True)
        thr.start()

    def listen_asynchronously(self):
        func_info = inspect.currentframe().f_back.f_code
        if self.bus is None:
            logging.warning(
                "[{}]: Must set bus first".format(func_info.co_name))
            return
        # job_callback_func = self.can_message_log_callback
        listeners = [self.update_can_data_callback]  # , job_callback_func]
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        logging.info("Starting the notifier loop...")
        self.notifier = can.Notifier(self.bus, listeners, loop=self.loop)
        if not self.loop.is_running():
            try:
                self.loop.run_forever()
            except can.CanError as e:
                logging.error("Error while listening. Details: {}".format(e))
            except Exception as e:
                logging.error("Error while listening. Details: {}".format(e))

    def stop_async_listener(self, inside_call: bool = False):
        if self.notifier is not None:
            logging.info("Shutting down the background loop...")
            self.logging_ = False
            self.usbWriter.close()
            self.notifier.stop()
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.listener_thread.join()
            self.loop = None
            self.notifier = None
            self.listener_thread = None
            logging.info("Background listener is shutdown.")
        elif not inside_call:
            logging.info("No listeners are running...")

    def update_can_data_callback(self, msg: can.Message):
        print("id: {}, data: {}".format(msg.arbitration_id, msg.data))
        if msg.arbitration_id in self.can_messages.keys():
            logging.info("Updating watched CAN message: {}".format(msg))
            self.can_messages[msg.arbitration_id] = msg.data
            # logging.info("Skipping CAN message (not watched): {}".format(msg))

    def can_message_log_callback(self, msg: can.Message):
        print(msg)
        CANListener.print_postproc()

    def send_message(self, arb_id, data):
        can_message = can.Message(arbitration_id=arb_id, data=data)
        try:
            self.bus.send(can_message)
        except can.CanError as canErr:
            logging.error(
                "Error while sending a CAN message {}".format(canErr))

    def start_watcher(self) -> Thread:
        if (self.watcher_thread is not None and self.watcher_thread.is_alive()):
            logging.info(
                "A watcher thread is already running. Shutting it down..")
            self.stop_watcher()
        self.watcher_thread = Thread(target=self.watch_async)
        self.watcher_thread.start()
        self._watcher_start_time = time.time()
        return self.watcher_thread

    def watch_async(self):
        self.watched_msg_counter = 0
        listeners = [self.watch_counter]
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.watcher_loop = asyncio.get_event_loop()
        logging.info("Starting the watcher loop...")
        self.watcher_notifier = can.Notifier(
            self.bus, listeners, loop=self.watcher_loop)
        if not self.watcher_loop.is_running():
            self.watcher_loop.run_forever()

    def watch_counter(self, msg: can.Message):
        elapsed_time = time.time() - self._watcher_start_time
        self.watched_msg_counter += 1
        print("# of messages received: {0} in {1:.4f} secs".format(
            self.watched_msg_counter, elapsed_time), end="\r", flush=True)

    def stop_watcher(self):
        print("")
        if self.watcher_notifier is not None:
            logging.info("Shutting down the watcher loop...")
            self.watcher_notifier.stop()
            self.watcher_loop.call_soon_threadsafe(self.watcher_loop.stop)
            self.watcher_thread.join()
            self.watcher_loop = None
            self.watcher_notifier = None
            self.watcher_thread = None

    @staticmethod
    def print_postproc():
        print("Finished processing.")

    @staticmethod
    def addon_can_cb(msg):
        print("Addon CAN callback: {}".format(msg))
