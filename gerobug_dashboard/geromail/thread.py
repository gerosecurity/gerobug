import threading, logging
from . import geroparser


# LOGGING INITIATION
logging.basicConfig(filename='log/gerobug.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class RunGeromailThread(threading.Thread):

    def __init__(self, total):
        self.total = total
        threading.Thread.__init__(self)
    
    def run(self):
        try:
            while True:
                running = geroparser.check_run()
                if running == False:
                    logging.debug("[LOG] Starting Geroparser...")
                    geroparser.run()
                else:
                    logging.warning("Geroparser Check Run = " + str(running))
        
        except Exception as e:
            logging.error("Geroparser Thread Failed: " + str(e))
