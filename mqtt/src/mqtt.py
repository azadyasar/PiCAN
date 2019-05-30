import yaml
import time
import paho.mqtt.client as mqtt
import logging as logger

logger.getLogger().setLevel(logger.DEBUG)

# Config keyword
BROKER   = 'Broker'
HOST     = 'host'
PORT     = 'port'
UNAME    = 'username'
PASSWORD = 'password'

FILEPATH = "./config_mqtt.yaml"

class Config:
    def __init__(self, filepath):
        self.filepath = filepath
        
    def read_config(self):
        with open(self.filepath, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as error:
                print("Error occured while parsing {}".format(self.filepath))
                return None
                
class MqttClient:
    def __init__(self, mqtt_config={}):
        if len(mqtt_config.keys()) is not 0:
            self.host   = mqtt_config[BROKER][HOST]
            self.port     = mqtt_config[BROKER][PORT]
            self.uname    = mqtt_config[BROKER][UNAME]
            self.password = mqtt_config[BROKER][PASSWORD]
        else:
            self.host   = None
            self.port     = None
            self.uname    = None
            self.password = None
            
    def on_connect(client, userdata, flags, rc):
        logger.info("Client connected to the broker client: {}, userdata: {}, flags: {}, rc: {}".format(client, userdata, flags, rc))
        # Subscribing in on_connect() means that if we lose the connection and reconnect then
        # subscriptions will be renewed
        client.subscribe("$SYS/#")
        client.subscribe("iphone")
        
    def on_message(client, userdata, message):
        logger.info("Message received. client: {}, userdata: {}, message: {}".format(client, userdata, message))
        logger.info("Topic: {} - Payload: {}".format(message.topic, message.payload))
        
    '''
    0: success, connection accepted
    1: connection refused, bad protocol
    2: refused, client-id error
    3: refused, service unavailable
    4: refused, bad username and password
    5: refused, not authorized
    '''
    def connect(self):
        self.client = mqtt.Client("rpi_mqtt")
        self.client.on_connect = MqttClient.on_connect
        self.client.on_message = MqttClient.on_message
        self.client.username_pw_set(self.uname, self.password)
        self.client.connect(self.host, self.port)
        self.client.loop_forever()

if __name__ == "__main__":
    config = Config(FILEPATH)
    config_dict = config.read_config()
    
    mqtt_client = MqttClient(config_dict)
    mqtt_client.connect()
        
        
        
        
        
        
        
        
        
        
        
        
                    
