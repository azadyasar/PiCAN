from socket import gaierror
import asyncio
import logging as logger
import sys
import os
import yaml
import time
import paho.mqtt.client as mqtt
import threading
import re
# _pattern_type is no longer available starting from version 3.7
if sys.version_info[1] >= 7:
    re._pattern_type = re.Pattern
# from pynput import keyboard
try:
    from .mqtt_constants import CONST as MQTT_CONSTANTS
except ImportError:
    from mqtt_constants import CONST as MQTT_CONSTANTS

logger.getLogger().setLevel(logger.DEBUG)


def terminate(msg="No message provided"):
    logger.warning("Terminating... [Message]: {}".format(msg))
    sys.exit(1)


# class MQTTKeyboardListener:
#     def __init__(self, mqtt):
#         self.mqtt = mqtt
#         self.keyboard_listener = None

#     def on_press(self, key: keyboard.Key):
#         try:
#             if key.char == 's' or key.char == 'S':
#                 if self.mqtt:
#                     if not self.mqtt.is_connected:
#                         logger.info(
#                             "MQTT Client is not connected. Can't publish.")
#                         return
#                 else:
#                     logger.info("MQTT Client is not initialized.")
#                     return

#                 # print("Topic: ")
#                 # topic = input()
#                 # print("Message: ")
#                 # message = input()
#                 print("Publishing +/+/test - Hello")
#                 self.mqtt.publish(topic="test", payload="Hello")
#         except AttributeError:
#             pass
#         finally:
#             pass

#     def on_release(self, key: keyboard.Key):
#         if key == keyboard.Key.esc:
#             logger.info("Exiting...")
#             self.keyboard_listener.stop()
#             return False

#     def start(self):
#         with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as key_listener:
#             self.keyboard_listener = key_listener
#             logger.info("Keyboard listener is activated.")
#             key_listener.join()
#             self.mqtt.shutdown()


class Config:
    def __init__(self, filepath):
        self.filepath = filepath

    def read_config(self):
        try:
            with open(self.filepath, "r") as stream:
                try:
                    return yaml.safe_load(stream)
                except yaml.YAMLError as error:
                    print("Error occured while parsing {}\n\tDetails: {}".format(
                        self.filepath, error))
                    return None
        except FileNotFoundError as ioErr:
            logger.error(
                "MQTT config file not found\n\tDetails: {}".format(ioErr))
            terminate()


class MqttClient:
    def __init__(self, mqtt_config: dict = None):
        if mqtt_config is None:
            config = Config(MQTT_CONSTANTS.MQTT_CONFIG_FILEPATH)
            mqtt_config = config.read_config()
        if len(mqtt_config.keys()) is not 0:
            try:
                self.host = mqtt_config[MQTT_CONSTANTS.BROKER_STR][MQTT_CONSTANTS.HOST_STR]
                self.port = mqtt_config[MQTT_CONSTANTS.BROKER_STR][MQTT_CONSTANTS.PORT_STR]
                self.uname = mqtt_config[MQTT_CONSTANTS.BROKER_STR][MQTT_CONSTANTS.UNAME_STR]
                self.password = mqtt_config[MQTT_CONSTANTS.BROKER_STR][MQTT_CONSTANTS.PASSWORD_STR]
                self.prefix = "avl/"
                self.id = mqtt_config[MQTT_CONSTANTS.CLIENT_STR][MQTT_CONSTANTS.ID_STR]
                self.sub_topics = mqtt_config[MQTT_CONSTANTS.CLIENT_STR][MQTT_CONSTANTS.SUB_TOPICS_STR]
                self.pub_topics = mqtt_config[MQTT_CONSTANTS.CLIENT_STR][MQTT_CONSTANTS.PUB_TOPICS_STR]
                self.hb_period = mqtt_config[MQTT_CONSTANTS.CLIENT_STR][MQTT_CONSTANTS.HEARTBEAT_PERIOD_STR]
            except KeyError as key_error:
                logger.error(
                    "Error while reading the config file -{}-.\n\tDetails: {} attribute is not properly set".format(MQTT_CONSTANTS.MQTT_CONFIG_FILEPATH, key_error))
                self.init_attributes_default()
        else:
            self.init_attributes_default()
        # Regex can be used if custom message->action mechanism is desired
        # self.topic_func_map = {re.compile(".*/add_sub_topic"): self.add_sub_topic}
        self.is_connected = False
        self.topic_func_map = {}
        # self.topic_func_map = {re.compile(".*/location"): [self.location_cb]}

    def init_attributes_default(self):
        self.host = None
        self.port = None
        self.uname = None
        self.password = None
        self.prefix = "avl/"
        self.id = "avl_rpi"
        self.sub_topics = []
        self.pub_topics = []
        self.hb_period = 15

    def on_connect(self, client, userdata, flags, rc):
        self.is_connected = True
        logger.info("Client connected to the broker {}".format(self.host))
        # Subscribing in on_connect() means that if we lose the connection and reconnect then
        # subscriptions will be renewed
        logger.info(
            "Subscribing to the following topics: {}".format(self.sub_topics))
        for sub_topic in self.sub_topics:
            self.client.subscribe(sub_topic)
        self.client.publish(self.id + "/message", "Greetings from AVL RPi")
        self.heartbeat()

    def on_disconnect(self, client, userdata, rc=0):
        self.is_connected = False
        logger.info("{} disconnected with result code: {}".format(self.id, rc))
        client.loop_stop()

    def on_message(self, client, userdata, message):
        logger.info(
            "Incoming message: Topic: {} - Payload: {}".format(message.topic, message.payload))

        for topic_re in self.topic_func_map:
            if topic_re.match(message.topic) is not None:
                # Iterate through all the registered callbacks of the corresponding
                # regex-topic
                for callback in self.topic_func_map[topic_re]:
                    callback(message)
            else:
                logger.info("{} does not match {}".format(
                    topic_re, message.topic))

    def heartbeat(self):
        logger.info("### Heartbeat ###")
        self.client.publish(self.id + "/heartbeat", "ON", retain=False, qos=1)
        threading.Timer(self.hb_period, self.heartbeat).start()

    def publish(self, topic, payload, qos: int = 0) -> mqtt.MQTTMessageInfo:
        if topic is None:
            logger.warning("Can't publish messages with no topic.")
            return
        return self.client.publish(topic=self.prefix + topic, payload=payload, qos=qos)

    # Registers a callback to the specified topic. When a message having the specified
    # topic arrives, the callback will be called.
    def register_cb(self, _sub_topic: re._pattern_type or str, callback) -> bool:
        # Temporary solution. TODO Decide whether to use regex, str or both
        if not isinstance(_sub_topic, re._pattern_type):
            _sub_topic = re.compile(_sub_topic)
        # if the given sub_topic is a regex check if any of the subscribed topics is a match for
        # the regex, warn otherwise
        if isinstance(_sub_topic, re._pattern_type):
            matched_topics = list(
                filter(lambda topic: _sub_topic.match(topic), self.sub_topics))
            if len(matched_topics) is 0:
                logger.warning("Registering a callback that is not in the subscribed topics. sub_topics: {}, sub_topic: {}".format(
                    self.sub_topics, _sub_topic))
                # CHECK Should we return false? Might be the case that the registered topic will
                # be subscribed in the future
                return False
        # this condition will never hold True as we are converting str to regex
        # TODO either remove or allow str arguments
        elif isinstance(_sub_topic, str):
            if _sub_topic not in self.sub_topics:
                logger.warning("Registering a callback that is not in the subscribed topics. sub_topics: {}, sub_topic: {}".format(
                    self.sub_topics, _sub_topic))
                return False

        # Create the callback list if it does not exist. Append otherwise
        if _sub_topic not in self.topic_func_map:
            self.topic_func_map[_sub_topic] = [callback]
        # if the given regex-topic exists in the topic_func_map, its corresponding value
        # should be always a list of callbacks. TODO Can it be None? Should we check or skip?
        elif self.topic_func_map[_sub_topic] is None:
            self.topic_func_map[_sub_topic] = [callback]
        else:
            self.topic_func_map[_sub_topic].append(callback)

    def add_sub_topic(self, _topic):
        logger.info("Subscribing to {}".format(_topic))
        self.sub_topics.append(_topic)
        self.client.subscribe(_topic)

    def remove_sub_topic(self, _topic):
        try:
            self.sub_topics.remove(_topic)
        except ValueError as valueErr:
            logger.warning("Requested subscribe topic [{}] does not exist in the sub_topic list.\n\tDetails: {}".format(
                _topic, valueErr))
            pass

    # DEMO. To check if subscribed message - callback registering is working.
    def location_cb(self, message):
        logger.info(
            "Location CB -> topic: {}, payload: {}".format(message.topic, message.payload))

    '''
    0: success, connection accepted
    1: connection refused, bad protocol
    2: refused, client-id error
    3: refused, service unavailable
    4: refused, bad username and password
    5: refused, not authorized
    '''

    def connect(self, will=None):
        self.client = mqtt.Client(self.id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message  # MqttClient.on_message
        self.client.username_pw_set(self.uname, self.password)
        if will is not None:
            logger.info("Setting will of the client: {}".format(will))
            self.client.will_set("will", payload=will, qos=2, retain=False)
        conn_status = -1
        logger.info("Connecting to the {}".format(self.host))
        try:
            conn_status = self.client.connect(self.host, self.port)
        except gaierror as err:
            logger.error("Error while trying to connect to the {} Status: {}\n\tDetails: {}".format(
                self.host, conn_status, err))
            # terminate("Connection error")
            return False
        except ValueError as value_err:
            logger.error("Error while trying to connect to the {} Status: {}\n\tDetailst: {}".format(
                self.host, conn_status, value_err))
            return False
            # terminate(value_err)
        except TimeoutError as timeoutError:
            logger.error(
                "TimeoutError occured.\n\tDetails: {}".format(timeoutError))
            return False
            # terminate("Timeout")

        # self.client.loop_forever()
        self.client.loop_start()

    def shutdown(self):
        self.client.loop_stop()
        self.client.disconnect()


class MqttTest:
    def __init__(self, id):
        self.value = 0
        self.id = id

    def speed_cb(self, message):
        logger.info("MqttTest [{}]: Registered_CB -> topic: {}, paylaod: {}".format(
            self.id, message.topic, message.payload.decode("utf-8")))

    def test_register_cb(self, mqttClient: MqttClient):
        logger.info("Testing register_cb of {}".format(self.id))
        mqttClient.register_cb(".*test2", self.speed_cb)


def test_mqtt_registration(mqtt_client: MqttClient):
    mqtt_test1 = MqttTest("mqtt-test-1")
    mqtt_test1.test_register_cb(mqtt_client)
    mqtt_test2 = MqttTest("mqtt-test-2")
    mqtt_test2.test_register_cb(mqtt_client)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-id", "--id", default=None)
    args = vars(parser.parse_args())

    config = Config(MQTT_CONSTANTS.MQTT_CONFIG_FILEPATH)
    config_dict = config.read_config()

    mqtt_client = MqttClient(config_dict)
    if args["id"] is not None:
        logger.info("Setting MQTT Client id to {}".format(args["id"]))
        mqtt_client.id = args["id"]
    mqtt_client.connect()
    # ? mqtt_client.client._thread.join()

    # Testing if registration within the MqttClient works.
    # Remove once deployed to production
    # test_mqtt_registration(mqtt_client)

    # mqtt_keyboard_listener = MQTTKeyboardListener(mqtt_client)
    mqtt_keyboard_listener.start()
