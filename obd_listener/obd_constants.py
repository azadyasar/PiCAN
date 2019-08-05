import os 


class OBD_CONSTANTS:
    OBD_CONFIG_FILEPATH = os.path.dirname(
        os.path.realpath(__file__)) + "/config_obd.yaml"

    OBD_STR = "OBD"
    MESSAGES_STR = "messages"
    ID_STR = "ID"
    JOB_STR = "job"
    JOB_LOG_STR = "log"
    JOB_PUBLISH_STR = "publish"