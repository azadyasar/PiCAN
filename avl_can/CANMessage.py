'''
An abstract representation of a CAN message for higher level usage
'''

from datetime import datetime

class CANMessage:
    def __init__(self, id, desc, initial_data=None):
        self.id = id
        self.data = initial_data
        self.last_update = datetime.timestamp(datetime.now())
        self.description = desc
        
    def update_data(self, new_data):
        self.data = new_data
        self.last_update = datetime.timestamp(datetime.now())
