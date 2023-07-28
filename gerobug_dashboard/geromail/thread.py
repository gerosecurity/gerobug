import threading
from . import geroparser

class RunGeromailThread(threading.Thread):

    def __init__(self, total):
        self.total = total
        threading.Thread.__init__(self)
    
    def run(self):
        try:
            if geroparser.check_run() == False:
                geroparser.run()
        
        except Exception as e:
            print("[ERROR] Geroparser Thread Failed: " + e)
