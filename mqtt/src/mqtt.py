import sys
import yaml
import time
import paho.mqtt.client as mqtt
import threading
import re
import logging as logger

from socket import gaierror


logger.getLogger().setLevel(logger.DEBUG)

# Config keywords
BROKER_STR     = 'Broker'
HOST_STR       = 'host'
PORT_STR       = 'port'
UNAME_STR      = 'username'
PASSWORD_STR   = 'password'
CLIENT_STR     = 'Client'
ID_STR         = 'id'
SUB_TOPICS_STR = "subscribe_topics"
PUB_TOPICS_STR = "pub_topics"
NAME_STR       = "name"
QOS_STR        = "qos"

FILEPATH = "./config_mqtt.yaml"

def terminate(msg="No message"):
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
                    print("Error occured while parsing {}".format(self.filepath))
                    return None
        except FileNotFoundError as ioErr:
            logger.error("MQTT config file not found\nDetails: {}".format(ioErr))
            terminate()
                
class MqttClient:
    def __init__(self, mqtt_config={}):
        if len(mqtt_config.keys()) is not 0:
            self.host       = mqtt_config[BROKER_STR][HOST_STR]
            self.port       = mqtt_config[BROKER_STR][PORT_STR]
            self.uname      = mqtt_config[BROKER_STR][UNAME_STR]
            self.password   = mqtt_config[BROKER_STR][PASSWORD_STR]
            self.id         = mqtt_config[CLIENT_STR][ID_STR]
            self.sub_topics = mqtt_config[CLIENT_STR][SUB_TOPICS_STR]
            self.pub_topics = mqtt_config[CLIENT_STR][PUB_TOPICS_STR]
        else:
            self.host       = None
            self.port       = None
            self.uname      = None
            self.password   = None
            self.id         = "avl_rpi"
            self.sub_topics = []
            self.pub_topics = []
        self.topic_func_map = { re.compile(".*/add_sub_topic"): self.add_sub_topic }
            
    def on_connect(self, client, userdata, flags, rc):
        logger.info("Client connected to the broker client: {}, userdata: {}, flags: {}, rc: {}".format(client, userdata, flags, rc))
        # Subscribing in on_connect() means that if we lose the connection and reconnect then
        # subscriptions will be renewed
        logger.info("Subscribing to the following topics: {}".format(self.sub_topics))
        for sub_topic in self.sub_topics:
            self.client.subscribe(sub_topic)
        logger.info("Starting the heartbeat thread...")
        self.client.publish("avl_rpi/message", "Greetings from AVL Pi")
        self.heartbeat()
        
    def on_message(self, client, userdata, message):
        logger.info("Incoming message: Topic: {} - Payload: {}".format(message.topic, message.payload))

        for topic_re in self.topic_func_map:
            if topic_re.match(message.topic) is not None:
                logging.info("{} is in the topic_function map".format(message.topic))
                self.topic_func_map[message.topic](message.payload.decode("utf-8"))
            else:
                logging.info("{} does not match {}".format(topic_re, message.topic))
        
    def heartbeat(self):
        logger.info("### Heartbeat ###")
        self.client.publish(self.id + "/heartbeat", "ON", retain=True)
        threading.Timer(30, self.heartbeat).start()
        
    def add_sub_topic(self, _topic):
        logger.info("Subscribing to {}".format(_topic))
        self.sub_topics.append(_topic)
        
    def remove_sub_topic(self, _topic):
        try:
            self.sub_topics.remove(_topic)
        except ValueError as valueErr:
            logger.warning("Requested subscribe topic [{}] does not exist in the sub_topic list.\nDetails:".format(_topic, valueErr))         
            pass
        
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
        self.client.on_message = self.on_message # MqttClient.on_message
        self.client.username_pw_set(self.uname, self.password)
        if will is not None:
            self.client.will_set("will", payload=will, qos=2, retain=False)
        conn_status = -1
        try: 
            conn_status = self.client.connect(self.host, self.port)
        except gaierror as err:
            logger.error("Error while trying to connect to the {} Status: {}\nDetails: {}".format(self.host, conn_status, err))
            terminate("Connection error")
        
        self.client.loop_forever()

if __name__ == "__main__":
    config = Config(FILEPATH)
    config_dict = config.read_config()
    
    mqtt_client = MqttClient(config_dict)
    mqtt_client.connect()
        
        
        
        
        
        
        
        
        
        
        
        
                    
