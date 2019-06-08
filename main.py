from obd_listener import OBDTracker
from mqtt import MqttClient
import logging as logger
from pynput import keyboard

logger.getLogger(__name__).setLevel(logger.INFO)


def on_press(key: keyboard.Key):
    # try:
    #     print('Alphanumeric key {0} pressed'.format(key.char))
    # except AttributeError:
    #     print('Special key {0} pressed'.format(key))
    pass


def on_release(key: keyboard.Key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False


def start():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    logger.info("########## OBD Tracker ##########")

    logger.info("MqttClient is connecting to the broker")
    mqtt_client = MqttClient()
    mqtt_client.connect()

    obd_tracker = OBDTracker(mqtt_client=mqtt_client)
    obd_tracker.connect()
    obd_tracker.test_query()

    start()

    logger.info("Shutting down the OBDTracker...")
    obd_tracker.shut_down(reason="Shut down requested")
    logger.info("Shutting down the MqttClient...")
    mqtt_client.shut_down()

    # import asyncio
    # loop = asyncio.get_event_loop()
    # loop.run_forever()
    # obd_tracker.shut_down()
    logger.info("Program exiting...")
