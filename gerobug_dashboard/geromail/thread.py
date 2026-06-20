import threading, logging, time, traceback
from logging.handlers import TimedRotatingFileHandler
from . import geroparser


class RunGeromailThread(threading.Thread):

    CLEAN_DELAY = 5
    BASE_DELAY = 15
    MAX_DELAY = 300

    def __init__(self, total):
        self.total = total
        threading.Thread.__init__(self)

    def run(self):
        thread_id = threading.get_ident()
        fail_count = 0

        logging.getLogger("Gerologger").info(f"[THREAD-{thread_id}] Geroparser supervisor started")

        while True:
            try:
                geroparser.run()
                fail_count = 0
                delay = self.CLEAN_DELAY

            except (KeyboardInterrupt, SystemExit) as e:
                logging.getLogger("Gerologger").warning(f"[THREAD-{thread_id}] Stop signal ({type(e).__name__}) - exiting supervisor")
                break

            except BaseException as e:
                fail_count += 1
                delay = min(self.BASE_DELAY * (2 ** min(fail_count, 4)), self.MAX_DELAY)
                logging.getLogger("Gerologger").error(
                    f"[THREAD-{thread_id}] geroparser.run() crashed (fail #{fail_count}): "
                    f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                )

            logging.getLogger("Gerologger").info(f"[THREAD-{thread_id}] Restarting geroparser in {delay}s...")
            time.sleep(delay)

        logging.getLogger("Gerologger").error(f"[THREAD-{thread_id}] Supervisor stopped - exiting")
