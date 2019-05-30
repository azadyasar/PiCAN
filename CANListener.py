import can
from can.bus import BusState
import asyncio 

from threading import Thread
from CANMessage import CANMessage

import logging 
import inspect
logging.getLogger().setLevel(logging.INFO)

CAN_MESSAGES = 'CAN_MESSAGES'

class CANListener:
    def __init__(self, bus, config={}):
        self.bus = bus
        self.config = config
        self.set_config_msgids()
        self.init_can_messages()
        self.construct_message_id_mapping()
        
    def set_config_msgids(self):
        # Stores the CAN message IDs (retrieved from the config.yaml file)
        # and their corresponding descriptions. e.g., {1: 'eng_speed'}
        self.config_messages = {} # set()
        if self.config is not None and CAN_MESSAGES in self.config:
            for can_msg in self.config[CAN_MESSAGES]:
                logging.info("Reading {} message information".format(can_msg))
                id = self.config[CAN_MESSAGES][can_msg]['ID']
                self.config_messages[id] = can_msg
            logging.info("Constructed requested CAN message ID set: {}".format(self.config_messages))
        elif config is not None and CAN_MESSAGES not in self.config:
            logging.warning("config does not include {0}".format(CAN_MESSAGES))
    
    def init_can_messages(self):
        # Stores the latest CAN messages as CAN_Message_ID - CANMessage pairs
        self.can_data = {}
        for can_msg in self.config_messages:
            self.can_data[can_msg] = CANMessage(id=can_msg, desc=self.config_messages[can_msg])
            
    def construct_message_id_mapping(self):
        logging.debug("Constructing self.desc_id_dict")
        if self.config_messages is None:
            func_info = inspect.currentframe().f_back.f_code
            logging.warning("[{}]: Must initialize self.config_messages first".format(func_info.co_name))
        # Construct description-id map
        self.desc_id_dict = {}
        for msg_id in self.config_messages:
            self.desc_id_dict[self.config_messages[msg_id]] = msg_id
        
    def set_bus(self, bus):
        self.bus = bus
    
    def get_bus(self):
        return self.bus
        
    def print_config_msgs(self):
        for index, msg_id in enumerate(self.config_messages):
            print("{}: #{}: {}".format(index, msg_id, self.config_messages[msg_id]))
     
    def receive_all(self):
        try:
            print("Started listening to the all CAN messages. Hit CTRL+C to stop")
            while True:
                msg = self.bus.recv(1) # 1 sec timeout
                if msg is not None:
                    print(msg)
        except KeyboardInterrupt:
            print("KeyboardInterrupt! Stopped listening to the CAN bus")   
            pass
    
    '''
    Filters out the CAN messages that are not in the config.yaml file.
    '''
    def receive_config_msgs(self):
        try:
            print("Started listening to the requested CAN messages. Hit CTRL+C to stop")
            print("Requested CAN message IDs: {}".format(self.config_messages))
            while True:
                msg = self.bus.recv(1)
                if msg is not None and msg.arbitration_id in self.config_messages:
                    print(msg)
                elif msg is not None:
                    print("[DEBUG] Message is not in the requested messages:\n{}".format(msg))
        except KeyboardInterrupt:
            print("keyboardInterrupt! Stopped listening to the CN bus")
            pass
    
    def start_async_listener(self):
        loop = asyncio.get_event_loop()
        
    def __start_background_loop(self, loop):
        def run_forever(loop):
            listeners = [self.listen_async_cb]
            loop = asyncio.get_event_loop()
            notifier = can.Notifier(self.bus, listeners, loop=loop)
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                print("Interrupted")

        thread = Thread(target=run_forever, args=(loop,))
        thread.start()
        thread.join()
    
    def listen_asynchronously(self):
        func_info = inspect.currentframe().f_back.f_code
        if self.bus is None:
            logging.warning("[{}]: Must set bus first".format(func_info.co_name))
            return
        listeners = [self.listen_async_cb]
        loop = asyncio.get_event_loop()
        notifier = can.Notifier(self.bus, listeners, loop=loop)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("Interrupted")
    
    def listen_async_cb(self, msg):
        print(msg)
    
    
