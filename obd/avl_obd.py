import sys
import obd
import logging as logger
import yaml
from mqtt import MqttClient

logger.getLogger(__name__).setLevel(logger.DEBUG)

OBD_CONFIG_FILEPATH = "obd/config_obd.yaml"

# Config keyword
OBD_STR = "OBD"
MESSAGES_STR = "messages"
ID_STR = "ID"
JOB_STR = "job"
JOB_LOG_STR = "log"
JOB_PUBLISH_STR = "publish"


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
            logger.error("OBD Config file not found in {}\nDetails: {}".format(
                self.filepath, ioErr))
            terminate(ioErr)
        except yaml.YAMLError as yaml_err:
            logger.error("Error occured while parsing {}\nDetails: {}".format(
                self.filepath, yaml_err))
            terminate()

    @staticmethod
    def read_config_st(filepath):
        try:
            with open(filepath, "r") as stream:
                return yaml.safe_load(stream)
        except FileNotFoundError as ioErr:
            logger.error("OBD Config file not found in {}\nDetails: {}".format(
                filepath, ioErr))
            terminate(ioErr)
        except yaml.YAMLError as yaml_err:
            logger.error("Error occured while parsing {}\nDetails: {}".format(
                filepath, yaml_err))
            terminate()


class OBDTracker:
    def __init__(self, config_dict: dict or str = None, mqtt_client: MqttClient = None):
        self.id = 'obd-test'
        self.mqtt_client = mqtt_client
        self.set_up_config(config_dict)

    # `config` can be either a file path or a config dict
    def set_up_config(self, config=None):
        if config is None:
            config = OBD_CONFIG_FILEPATH
        if isinstance(config, str):
            config = OBDConfig.read_config_st(config)
        self.config = config
        self.id = config[OBD_STR][ID_STR]
        self.job = config[OBD_STR][JOB_STR]
        logger.info("OBDTracker job: {}".format(self.job))
        self.obd_messages = config[OBD_STR][MESSAGES_STR]

        self.obd_response_value_dict = {}
        for obd_message in self.obd_messages:
            self.obd_response_value_dict[obd_message] = None

    def print_supported_commands(self):
        if self.connection is not None and self.connection.is_connected():
            logger.info("Supported commands: {}".format(
                self.connection.supported_commands))
        else:
            logger.info("Can't get supported commands while disconnected")

    def connect(self, print_info: bool = True):
        self.connection = obd.Async()
        if print_info:
            self.print_supported_commands()

        if self.connection is None or not self.connection.is_connected():
            logger.warning("Unable to subscribe to the OBD messages")
            return
        self.watch_obd_messages()
        # Start the asynchronous event loop
        self.connection.start()

    def watch_obd_messages(self) -> bool:
        if self.job is 'log' and logger.getLogger().level <= logger.INFO:
            logger.warning("OBDListener is assigned to log incoming messages. But the logger level is {}".format(
                logger.getLevelName(logger.getLogger().level)))
            return False
        elif self.job is 'publish' and (self.mqtt_client is None or self.mqtt_client.is_connected()):
            logger.warning("OBDListener is assigned to publish incoming messages through MQTT." +
                           " But the MqttClient is None.")
            return False

        logger.info("OBD tracker subscribing to the following OBD messages: {}".format(
            self.obd_messages))
        callback_func = self.obd_response_callback_log if self.job is 'log' else self.obd_response_callback_publish
        for obd_message in self.obd_messages:
            self.connection.watch(
                obd.commands[obd_message], callback=callback_func)
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
        logger.info("[TEST] Querying the car. Status: {}".format(
            self.connection.status()))
        rpm_cmd = obd.commands['RPM']
        response = self.connection.query(rpm_cmd)
        logger.info("[TEST] Query response.value = {}".format(response.value))

    def set_mqtt_client(self, mqtt_client: MqttClient):
        self.mqtt_client = mqtt_client

    def shut_down(self, reason: str = None):
        logger.info(
            "Shutting down the OBD connection. Reason = {}".format(reason))
        self.connection.close()


if __name__ == "__main__":
    config = OBDConfig(OBD_CONFIG_FILEPATH)
    config_dict = config.read_config()

    obd_tracker = OBDTracker(config_dict)
    obd_tracker.connect()
    obd_tracker.test_query()
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_forever()
    logger.info("End of line")
