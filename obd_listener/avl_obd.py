import sys
import os
import obd
import logging as logger
import yaml
from mqtt import MqttClient

from serial.serialutil import SerialException

try:
    from .obd_constants import OBD_CONSTANTS
except ImportError:
    from obd_constants import OBD_CONSTANTS

logger.getLogger(__name__).setLevel(logger.DEBUG)


def terminate(msg="No message provided"):
    logger.warning("Terminating... [Message]: {}".format(msg))
    sys.exit(1)


class OBDConfig:
    def __init__(self, filepath):
        self.filepath = filepath

    def read_config(self):
        try:
            with open(self.filepath, "r") as stream:
                return yaml.safe_load(stream)
        except FileNotFoundError as ioErr:
            logger.error("OBD Config file not found in {}\n\tDetails: {}".format(
                self.filepath, ioErr))
            terminate(ioErr)
        except yaml.YAMLError as yaml_err:
            logger.error("Error occured while parsing {}\n\tDetails: {}".format(
                self.filepath, yaml_err))
            terminate()

    @staticmethod
    def read_config_st(filepath):
        try:
            with open(filepath, "r") as stream:
                return yaml.safe_load(stream)
        except FileNotFoundError as ioErr:
            logger.error("OBD Config file not found in {}\n\tDetails: {}".format(
                filepath, ioErr))
            terminate(ioErr)
        except yaml.YAMLError as yaml_err:
            logger.error("Error occured while parsing {}\n\tDetails: {}".format(
                filepath, yaml_err))
            terminate()


class OBDTracker:
    def __init__(self, config_dict: dict or str = None, mqtt_client: MqttClient = None):
        self.id = 'obd-test'
        self.mqtt_client = mqtt_client
        self.set_up_config(config_dict)
        self.connection = None

    # `config` can be either a file path or a config dict
    def set_up_config(self, config=None):
        if config is None:
            config = OBD_CONSTANTS.OBD_CONFIG_FILEPATH
        if isinstance(config, str):
            config = OBDConfig.read_config_st(config)
        self.config = config
        self.id = config[OBD_CONSTANTS.OBD_STR][OBD_CONSTANTS.ID_STR]
        self.job = config[OBD_CONSTANTS.OBD_STR][OBD_CONSTANTS.JOB_STR]
        logger.info("OBDTracker job: {}".format(self.job))
        self.obd_messages = config[OBD_CONSTANTS.OBD_STR][OBD_CONSTANTS.MESSAGES_STR]

        self.obd_response_value_dict = {}
        for obd_message in self.obd_messages:
            self.obd_response_value_dict[obd_message] = None

    def print_supported_commands(self):
        if self.connection is not None and self.connection.is_connected():
            logger.info("OBD supported commands: {}".format(
                self.connection.supported_commands))
        else:
            logger.info("Can't get supported commands while disconnected.")

    def connect(self, print_info: bool = True):
        try:
            self.connection = obd.Async()
        except SerialException as serialExc:
            logger.error(
                "Error while connecting to the OBD port.\n\tDetails: {}".format(serialExc))
            self.connection = None
            return False
        if print_info:
            self.print_supported_commands()

        if not (self.connection is not None and  self.connection.is_connected()):
            logger.warning("Unable to connect and  to the OBD messages")
            self.shutdown()
            return
        self.watch_obd_messages()

    def watch_obd_messages(self) -> bool:
        if self.job is 'log' and logger.getLogger().level <= logger.INFO:
            logger.warning("OBDListener is assigned to log incoming messages. But the logger level is {}".format(
                logger.getLevelName(logger.getLogger().level)))
            return False
        elif self.job is 'publish' and (self.mqtt_client is None or not self.mqtt_client.is_connected):
            logger.warning("OBDListener is assigned to publish incoming messages through MQTT." +
                           " But the MqttClient is None.")
            return False

        logger.info("OBD tracker subscribing to the following OBD messages: {}".format(
            self.obd_messages))
        callback_func = self.obd_response_callback_log if self.job == OBD_CONSTANTS.JOB_LOG_STR else self.obd_response_callback_publish
        # @TODO Check if obd_message is within the obd.commands
        for obd_message in self.obd_messages:
            if obd_message in obd.commands:
                self.connection.watch(
                    obd.commands[obd_message], callback=callback_func)
            else:
                logger.warning(
                    "Topic is not in the OBD Command List. Topic: {}".format(obd_message))
        return True

    def obd_response_callback_log(self, response: obd.OBDResponse):
        logger.info("{} [OBD_MSG_CB]: message = {}, value = {}".format(
            response.time, response, response.value))
        obd_message = response.command.name
        logger.info("response.command.name is = {}".format(obd_message))
        self.obd_response_value_dict[obd_message] = response.value

    def obd_response_callback_publish(self, response: obd.OBDResponse):
        logger.info("{} [OBD_MSG_CB]: message = {}, value = {}".format(
            response.time, response, response.value))
        obd_message_name = response.command.name
        logger.info("respon.command.name is = {}".format(obd_message_name))
        self.obd_response_value_dict[obd_message_name] = response.value
        self.mqtt_client.publish(
            topic=obd_message_name, payload=response.value)

    def test_query(self):
        if self.connection is None:
            return
        logger.info("[TEST] Querying the car. Status: {}".format(
            self.connection.status()))
        rpm_cmd = obd.commands['RPM']
        response = self.connection.query(rpm_cmd)
        logger.info("[TEST] Query response.value = {}".format(response.value))

    def set_mqtt_client(self, mqtt_client: MqttClient):
        self.mqtt_client = mqtt_client

    def shutdown(self, reason: str = None):
        logger.info(
            "Shutting down the OBD connection. Reason = {}".format(reason))
        if self.connection is not None:
            self.connection.close()

    """
    Declared and not implemented because the following functions are required for the KeyboardListener
    """
    def send_message(self, arb_id, data):
        pass

    def listen_async(self):
        if self.connection is not None and self.connection.is_connected():
            # Start the asynchronous event loop
            self.connection.start()
        else:
            logger.warning("Connect to a OBD Network first!")

    def stop_listener(self):
        if self.connection is not None and self.connection.is_connected():
            # Start the asynchronous event loop
            self.connection.stop()
        else:
            logger.warning("No OBD connections found.")


if __name__ == "__main__":
    config = OBDConfig(OBD_CONSTANTS.OBD_CONFIG_FILEPATH)
    config_dict = config.read_config()

    obd_tracker = OBDTracker(config_dict)
    obd_tracker.connect()
    obd_tracker.test_query()
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_forever()
    obd_tracker.shutdown()
    logger.info("End of line")
