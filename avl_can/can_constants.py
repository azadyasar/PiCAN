import os


class CAN_CONSTANTS:

    NETWORK_STR = "Network"
    BUSTYPE_STR = "bustype"
    CHANNEL_STR = "channel"
    BITRATE_STR = "bitrate"
    CONFIG_FILEPATH = os.path.dirname(
        os.path.realpath(__file__)) + "/config_can.yaml"
    CAN_MESSAGES_STR = "CAN_MESSAGES"
    ID_STR = "id"
    DESC_STR = "desc"
    REL_BYTES_STR = "rel_bytes"
    JOB_STR = "Job"
    JOB_LOG_STR = "log"
    JOB_PUBLISH_STR = "publish"

