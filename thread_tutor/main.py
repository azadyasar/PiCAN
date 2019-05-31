import logging
import threading
import time
import concurrent.futures


def thread_func(name):
    logging.info("Thread {}: starting".format(name))
    time.sleep(5 - name)
    logging.info("Thread {}: finished".format(name))
    
def test_basic_threading():
    logging.info("Main: before creating a thread")
    #  x = threading.Thread(target=thread_func, args=(1,))
    x = threading.Thread(target=thread_func, args=(1,), daemon=True)
    logging.info("Main: before running the thread")
    x.start()
    logging.info("Main: Wait for the thread to finish")
    # x.join()
    logging.info("Main: Finished waiting")
    
def test_threadpoolexecutor():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(thread_func, range(3))
    
    
# Demonstrating locks for race conditions
class FakeDB:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()
        
    def locked_update(self, name):
        logging.info("Before update of %s value: %d", name, self.value)
        logging.info("Thread %s: starting update", name)
        with self._lock:
            logging.info("Thread %s has lock", name)
            local_copy = self.value
            local_copy += 1 
            time.sleep(1)
            self.value = local_copy
            logging.info("Thread %s about to release lock", name)
        logging.info("Thread %s after release", name)
        logging.info("After update of %s value: %d", name, self.value)
        
    def test_lock(db):
        logging.info("Testing locked update.. value: %d", db.value)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for index in range(2):
                executor.submit(db.locked_update, index)
        logging.info("Testing locked update finished.. value: %d", db.value)
           
    
    
if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    # test_basic_threading()
    #    test_threadpoolexecutor()
    db = FakeDB()
    FakeDB.test_lock(db)

