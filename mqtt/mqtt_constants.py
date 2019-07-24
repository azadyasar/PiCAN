import os

# Config keywords


class CONST:

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

    MQTT_CONFIG_FILEPATH = os.path.dirname(
        os.path.realpath(__file__)) + "/config_mqtt.yaml"
