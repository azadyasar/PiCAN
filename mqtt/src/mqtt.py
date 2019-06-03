import sys
import yaml
import time
import paho.mqtt.client as mqtt
import threading
import re
import logging as logger
import asyncio

from socket import gaierror


logger.getLogger().setLevel(logger.DEBUG)

# Config keywords
BROKER_STR = 'Broker'
HOST_STR = 'host'
PORT_STR = 'port'
UNAME_STR = 'username'
PASSWORD_STR = 'password'
CLIENT_STR = 'Client'
ID_STR = 'id'
SUB_TOPICS_STR = "subscribe_topics"
PUB_TOPICS_STR = "pub_topics"
NAME_STR = "name"
QOS_STR = "qos"
HEARTBEAT_PERIOD_STR = "heartbeat_period"

FILEPATH = "./config_mqtt.yaml"


def terminate(msg="No message provided"):
    logger.warning("Terminating... [Message]: {}".format(msg))
    sys.exit(1)


class Config:
    def __init__(self, filepath):
        self.filepath = filepath

    def read_config(self):
        try:
            with open(self.filepath, "r") as stream:
                try:
                    return yaml.safe_load(stream)
                except yaml.YAMLError as error:
                    print("Error occured while parsing {}\nDetails: {}".format(
                        self.filepath, error))
                    return None
        except FileNotFoundError as ioErr:
            logger.error(
                "MQTT config file not found\nDetails: {}".format(ioErr))
            terminate()


class MqttClient:
    def __init__(self, mqtt_config={}):
        if len(mqtt_config.keys()) is not 0:
            try:
                self.host = mqtt_config[BROKER_STR][HOST_STR]
                self.port = mqtt_config[BROKER_STR][PORT_STR]
                self.uname = mqtt_config[BROKER_STR][UNAME_STR]
                self.password = mqtt_config[BROKER_STR][PASSWORD_STR]
                self.id = mqtt_config[CLIENT_STR][ID_STR]
                self.sub_topics = mqtt_config[CLIENT_STR][SUB_TOPICS_STR]
                self.pub_topics = mqtt_config[CLIENT_STR][PUB_TOPICS_STR]
                self.hb_period = mqtt_config[CLIENT_STR][HEARTBEAT_PERIOD_STR]
            except KeyError as key_error:
                logger.error(
                    "Error while reading the config file -{}-.\nDetails: {} attribute is not properly set".format(FILEPATH, key_error))
                self.init_attributes_default()
        else:
            self.init_attributes_default()
        # Regex can be used if custom message->action mechanism are desired
        # self.topic_func_map = {re.compile(".*/add_sub_topic"): self.add_sub_topic}
        self.topic_func_map = {re.compile(".*/location"): [self.location_cb]}

    def init_attributes_default(self):
        self.host = None
        self.port = None
        self.uname = None
        self.password = None
        self.id = "avl_rpi"
        self.sub_topics = []
        self.pub_topics = []
        self.hb_period = 15

    def on_connect(self, client, userdata, flags, rc):
        logger.info("Client connected to the broker")
        # Subscribing in on_connect() means that if we lose the connection and reconnect then
        # subscriptions will be renewed
        logger.info(
            "Subscribing to the following topics: {}".format(self.sub_topics))
        for sub_topic in self.sub_topics:
            self.client.subscribe(sub_topic)
        self.client.publish(self.id + "/message", "Greetings from AVL RPi")
        self.heartbeat()

    def on_disconnect(self, client, userdata, rc=0):
        logger.info("Disconnecting with result code: {}".format(rc))
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
        self.client.publish(self.id + "/heartbeat", "ON", retain=True)
        threading.Timer(self.hb_period, self.heartbeat).start()

    def publish(self, topic, payload, qos: int = 0):
        if topic is None:
            return
        self.client.publish(topic=topic, payload=payload, qos=qos)

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
            logger.warning("Requested subscribe topic [{}] does not exist in the sub_topic list.\nDetails: {}".format(
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

    def connect(self, will="will not defined"):
        self.client = mqtt.Client(self.id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message  # MqttClient.on_message
        self.client.username_pw_set(self.uname, self.password)
        if will is not None:
            logger.info("Setting will of the client: {}".format(will))
            self.client.will_set("will", payload=will, qos=2, retain=False)
        conn_status = -1
        try:
            conn_status = self.client.connect(self.host, self.port)
        except gaierror as err:
            logger.error("Error while trying to connect to the {} Status: {}\nDetails: {}".format(
                self.host, conn_status, err))
            terminate("Connection error")
        except ValueError as value_err:
            logger.error("Error while trying to connect to the {} Status: {}\nDetailst: {}".format(
                self.host, conn_status, value_err))
            terminate(value_err)

        # self.client.loop_forever()
        self.client.loop_start()


class MqttTest:
    def __init__(self, id):
        self.value = 0
        self.id = id

    def speed_cb(self, message):
        logger.info("MqttTest [{}]: speed_cb -> topic: {}, paylaod: {}".format(
            self.id, message.topic, message.payload.decode("utf-8")))

    def test_register_cb(self, mqttClient: MqttClient):
        logger.info("Testing register_cb of {}".format(self.id))
        mqttClient.register_cb(".*speed", self.speed_cb)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-id", "--id", default=None)
    args = vars(parser.parse_args())

    config = Config(FILEPATH)
    config_dict = config.read_config()

    mqtt_client = MqttClient(config_dict)
    if args["id"] is not None:
        logger.info("Setting MQTT Client id to {}".format(args["id"]))
        mqtt_client.id = args["id"]
    mqtt_client.connect()

    # Testing if registration within the MqttClient works.
    # Remove once deployed to production
    mqttTest = MqttTest("mqtt-test-1")
    mqttTest.test_register_cb(mqtt_client)
    mqttTest2 = MqttTest("mqtt-test-2")
    mqttTest2.test_register_cb(mqtt_client)
    loop = asyncio.get_event_loop()
    loop.run_forever()
    logger.info("End of line")
