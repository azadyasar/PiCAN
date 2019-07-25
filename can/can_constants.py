import os


class CAN_CONSTANTS:

    NETWORK_STR = "Network"
    BUSTYPE_STR = "bustype"
    CHANNEL_STR = "channel"
    BITRATE_STR = "bitrate"
    CONFIG_FILEPATH = os.path.dirname(
        os.path.realpath(__file__)) + "/config_can.yaml"
    CAN_MESSAGES_STR = "CAN_MESSAGES"
