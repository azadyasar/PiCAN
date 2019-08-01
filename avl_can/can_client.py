import can
import logging
from mqtt import MqttClient

from .CANListener import CANListener
from .can_constants import CAN_CONSTANTS
from .can_config import Config
from .CANMessage import CANMessage

logging.getLogger().setLevel(logging.INFO)


class CANClient:
    def __init__(self, mqtt_client: MqttClient = None):
        self.config_dict = Config().read_config()
        # logging.info("CAN config file is read: {}".format(self.config_dict))

        self.bustype, self.channel, self.bitrate = self.config_dict[CAN_CONSTANTS.NETWORK_STR][CAN_CONSTANTS.BUSTYPE_STR], self.config_dict[CAN_CONSTANTS.NETWORK_STR][
            CAN_CONSTANTS.CHANNEL_STR], self.config_dict[CAN_CONSTANTS.NETWORK_STR][CAN_CONSTANTS.BITRATE_STR]
        logging.info("CAN connection parameters: Bustype: {}, Channel: {}, Bitrate: {}".format(
            self.bustype, self.channel, self.bitrate
        ))
        self.bus = None
        self.can_listener = None
        self.mqtt_client = mqtt_client

    def connect(self):
        try:
            self.bus = can.interface.Bus(
                channel=self.channel, bustype=self.bustype, bitrate=self.bitrate)
            logging.info("Connected to the CAN bus.")
        except OSError as osErr:
            logging.error(
                "Error while connecting to the CAN bus.\nDetails: {}".format(osErr))
            return False

        self.can_listener = CANListener(bus=self.bus, config=self.config_dict, mqtt_client=self.mqtt_client)
        return True

    def shutdown(self):
        if self.bus is not None:
            self.can_listener.stop_async_listener()
            self.bus.shutdown()

    def listen_async(self):
        if self.bus is None or self.can_listener is None:
            logging.warning("Connect to a CAN bus first.")
            return
        self.can_listener.start_background_listener()

    def stop_listener(self):
        if self.can_listener is None:
            logging.warning("No CAN listeners found.")
            return
        self.can_listener.stop_async_listener()

    def send_message(self, arb_id, data):
        if self.bus is None:
            logging.warning("Connect to a CAN bus first.")
            return
        can_message = can.Message(arbitration_id=arb_id, data=data)
        try:
            self.bus.send(can_message)
        except can.CanError as canErr:
            logging.error(
                "Error while sending a CAN message {}".format(canErr))
