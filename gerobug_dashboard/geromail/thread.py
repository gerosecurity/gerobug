import threading, logging, time
from logging.handlers import TimedRotatingFileHandler
from . import geroparser


class RunGeromailThread(threading.Thread):

    def __init__(self, total):
        self.total = total
        threading.Thread.__init__(self)
    
    def run(self):
        logging.getLogger("Gerologger").debug("[LOG] Starting Geroparser thread...")
        while True:
            try:
                geroparser.run()
            
            except Exception as e:
                logging.getLogger("Gerologger").error("Geroparser Thread Failed: " + str(e))
            
            time.sleep(30)

        logging.getLogger("Gerologger").error("Thread Loop Stopped")
