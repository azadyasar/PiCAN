import sys
import obd
import logging as logger
import yaml

logger.getLogger(__name__).setLevel(logger.DEBUG)

FILEPATH = "./config_obd.yaml"

# Config keyword
OBD_STR = "OBD"
MESSAGES_STR = "messages"


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


class OBDTracker:
    def __init__(self, config_dict):
        self.id = 'obd-test'
        self.obd_messages = config_dict[OBD_STR][MESSAGES_STR]
        self.obd_response_value_dict = {}
        for obd_message in self.obd_messages:
            self.obd_response_value_dict[obd_message] = None

    def connect(self):
        self.connection = obd.Async()
        self.watch_obd_messages()

    def watch_obd_messages(self):
        for obd_message in self.obd_messages:
            self.connection.watch(
                obd.commands[obd_message], self.obd_response_callback)

    def obd_response_callback(self, response: obd.OBDResponse):
        logger.info("{} [OBD_MSG_CB]: message = {}, value = {}".format(
            response.time, response, response.value))
        obd_message = response.command.name
        logger.info("OBD Message is {}".format(obd_message))
        self.obd_response_value_dict[obd_message] = response.value

    def test_query(self):
        logger.info("Status: {}".format(self.connection.status()))
        rpm_cmd = obd.commands.RPM


config = OBDConfig(FILEPATH)
config_dict = config.read_config()

obd_tracker = OBDTracker(config_dict)
obd_tracker.connect()
obd_tracker.test_query()
logger.info("End of line")
