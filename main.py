from obd_listener import OBDTracker
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
    parser.add_argument("-usb", "--saveusb", type=bool, default=True)
    parser.add_argument("-s", "--secure", type=bool, default=False)
    parser.add_argument("-br", "--bitrate", type=int, default=None)
    args = vars(parser.parse_args())

    backend = args["backend"]
    logger.info("Backend: {}".format(backend))

    use_mqtt = args["usemqtt"]
    save_to_usb = args["saveusb"]
    mqtt_client = None
    if use_mqtt is True:
        mqtt_client = MqttClient()
        logger.info("{} is connecting to the broker".format(mqtt_client.id))
        mqtt_client.connect()

    is_secured = args["secure"]
    if is_secured:
        logger.info(
            "You are running in secure mode which means you can publish messages into the CAN bus.")

    bitrate = args["bitrate"]

    client = None
    if save_to_usb:
        logger.info("Logging to USB...")
        from can_usb_logger import CANClient
    else:
        from avl_can import CANClient

    if backend == "can":
        if save_to_usb:
            client = CANClient(bitrate=bitrate)
        else:
            client = CANClient(mqtt_client=mqtt_client, bitrate=bitrate)
        client.connect()
    elif backend == "obd":
        client = OBDTracker(mqtt_client=mqtt_client)
        client.connect()
        client.test_query()
    else:
        logger.warning(
            "Unknown backend: {}. Possible backends: can, obd".format(backend))
        sys.exit(1)

    # keyboard_listener = KeyboardListener(client, is_secured)
    keyboard_listener = KeyboardListener(client, is_secured)
    keyboard_listener.start()
    logger.info("Stopped listening. Cleaning up..")
    if mqtt_client is not None:
        mqtt_client.shutdown()
