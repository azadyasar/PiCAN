from __future__ import print_function

import logging 
import time

import can

logging.getLogger().setLevel(logging.INFO)

def simple_periodic_send(bus):
    """
    Sends a message every 200ms with no explicit timeout
    Sleeps for 2 seconds then stops the task.
    """
    print("Starting to send a message every 200ms for 2s")
    msg = can.Message(arbitration_id=0x123, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=False)
    task = bus.send_periodic(msg, 0.20)
    try:
        assert isinstance(task, can.CyclicSendTaskABC)
    except Error as e:
        print(e)
        task.stop()
    time.sleep(2)
    task.stop()
    print("Stopped cyclic send")

