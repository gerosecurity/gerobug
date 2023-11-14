import threading, logging
from logging.handlers import TimedRotatingFileHandler
from . import geroparser



class RunGeromailThread(threading.Thread):

    def __init__(self, total):
        self.total = total
        threading.Thread.__init__(self)
    
    def run(self):
        while True:
            try:
                running = geroparser.check_run()
                if running == False:
                    logging.getLogger("Gerologger").debug("[LOG] Starting Geroparser...")
                    geroparser.run()
                else:
                    logging.getLogger("Gerologger").warning("Geroparser Check Run = " + str(running))
            
            except Exception as e:
                logging.getLogger("Gerologger").error("Geroparser Thread Failed: " + str(e))
