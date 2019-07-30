"""
Initialize with a YAML config filepath. Parses and returns
the config YAML file as a dict object

"""
try:
    from .can_constants import CAN_CONSTANTS
except ImportError:
    from can_constants import CAN_CONSTANTS
import os
import yaml
import logging

logging.getLogger().setLevel(logging.INFO)


class Config:

    def __init__(self, filename: str = None):
        self.filename = CAN_CONSTANTS.CONFIG_FILEPATH if filename is None else filename

    def set_filename(self, filename):
        self.filename = filename

    def read_config(self):
        try:
            with open(self.filename, "r") as stream:
                try:
                    return yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    logging.warning(
                        "Exception occured while parsing config file {}".format(exc))
                    return {}
        except FileNotFoundError:
            logging.warning("Config file not found")
            return {}

    @staticmethod
    def read_config_st(filename):
        try:
            with open(filename, "r") as stream:
                try:
                    return yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    logging.warning(
                        "Exception occured while parsing config file {}".format(exc))
                    return {}
        except FileNotFoundError:
            logging.warning("Config file not found")
            return {}
