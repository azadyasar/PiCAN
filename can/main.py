import can
import logging
logging.getLogger().setLevel(logging.INFO)

from config import Config
from CANListener import CANListener

filepath = "./config.yaml"

config_dict = Config(filepath).read_config()
logging.info("Config dict is read: {}".format(config_dict))

bustype, channel = 'socketcan', 'can0' 
bus = can.interface.Bus(channel=channel, bustype=bustype, bitrate=500000)
can_listener = CANListener(bus, config_dict) 

logging.info("Starting async listener")
# can_listener.listen_asynchronously()
can_listener.start_async_listener()
logging.info("Started..")




