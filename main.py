from obd_listener import OBDTracker
from avl_can import CANClient
from mqtt import MqttClient
from KeyboardListener import KeyboardListener
import logging as logger
import sys

import argparse

logger.getLogger(__name__).setLevel(logger.INFO)

if __name__ == "__main__":
    logger.info("########## OBD/CAN Listener ##########")

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--backend", type=str, default="can")
    parser.add_argument("-mqtt", "--usemqtt", type=bool, default=False)
    args = vars(parser.parse_args())

    backend = args["backend"]
    logger.info("Backend: {}".format(backend))
    use_mqtt = args["usemqtt"]

    mqtt_client = None
    if use_mqtt is True:
        mqtt_client = MqttClient()
        logger.info("{} is connecting to the broker".format(mqtt_client.id))
        mqtt_client.connect()

    client = None
    if backend == "can":
        client = CANClient(mqtt_client=mqtt_client)
        client.connect()
    elif backend == "obd":
        client = OBDTracker(mqtt_client=mqtt_client)
        client.connect()
        client.test_query()
    else:
        logger.warning(
            "Unknown backend: {}. Possible backends: can, obd".format(backend))
        sys.exit(1)

    keyboard_listener = KeyboardListener(client=client)

    keyboard_listener.start()
    logger.info("Stopped listening. Cleaning up..")
    if mqtt_client is not None:
        mqtt_client.shutdown()
