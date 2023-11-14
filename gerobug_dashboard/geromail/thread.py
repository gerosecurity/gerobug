import threading, logging
from logging.handlers import TimedRotatingFileHandler
from . import geroparser


# GEROLOGGER INITIATION
gerologger = logging.getLogger("Gerobug Log")
log_handler = TimedRotatingFileHandler('log/gerobug.log', when='midnight', backupCount=3)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
gerologger.setLevel(logging.DEBUG)
gerologger.addHandler(log_handler)

class RunGeromailThread(threading.Thread):

    def __init__(self, total):
        self.total = total
        threading.Thread.__init__(self)
    
    def run(self):
        while True:
            try:
                running = geroparser.check_run()
                if running == False:
                    gerologger.debug("[LOG] Starting Geroparser...")
                    geroparser.run()
                else:
                    gerologger.warning("Geroparser Check Run = " + str(running))
            
            except Exception as e:
                gerologger.error("Geroparser Thread Failed: " + str(e))
