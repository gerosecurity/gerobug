import time
import logging
from logging.handlers import TimedRotatingFileHandler
from dashboards.models import Blacklist, Watchlist, BlacklistRule



# DEFAULT RULE ==> IF THERE ARE MORE THAN 10 EMAILS WITH <= 1 MINUTE INTERVAL, BLACKLIST FOR 1 HOUR
# MAX COUNTER BEFORE BLACKLIST (DEFAULT 10)
# BUFFER FOR COUNTER INTERVALS (DEFAULT 60 SECONDS)
# BUFFER FOR BLACKLIST PERIOD (DEFAULT 3600 SECONDS / 1 HOUR)
# BUFFER FOR CLEANING WATCHLIST (DEFAULT 86400 SECONDS / 24 HOUR)



# GEROLOGGER INITIATION
gerologger = logging.getLogger("Gerobug Log")
log_handler = TimedRotatingFileHandler('log/gerobug.log', when='midnight', backupCount=3)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
gerologger.setLevel(logging.DEBUG)
gerologger.addHandler(log_handler)


# BLACKLIST SPAM EMAIL
def check_blacklist(email):
    if Blacklist.objects.filter(email=email).exists():
        BLACKLISTRULE = BlacklistRule.objects.get(rule_id=1)
        blacklisted = Blacklist.objects.get(email=email)
        ct = int(time.time())
        diff =  ct - blacklisted.time 
    
        if diff < BLACKLISTRULE.buffer_blacklist:
            remaining = (blacklisted.time + BLACKLISTRULE.buffer_blacklist) - ct
            gerologger.warning("Email Blacklisted Due to Spam Activity (Release in "+str(remaining)+" seconds)")
            gerologger.info('============================')

            # LIMIT ONLY 1 NOTIFICATION TO MITIGATE ABUSE
            if blacklisted.informed == 0:
                blacklisted.informed = 1
                blacklisted.save()
                return True, remaining, True
            else:
                return True, "", False

        else:
            # RELEASE THE BLACKLIST STATUS
            blacklisted.delete()
            gerologger.info("Email Released from Blacklist")
            return False, "", False
    
    else:
        return False, "", False

# BLACKLIST SPAM EMAIL
def blacklist(email):
    black = Blacklist()
    black.email = email
    black.time = int(time.time())
    black.save()

# MONITOR SUSPECT EMAIL
def monitor(email, ts):
    # IF EMAIL ALREADY BLACKLISTED
    if Blacklist.objects.filter(email=email).exists():
        pass

    elif Watchlist.objects.filter(email=email).exists():
        BLACKLISTRULE = BlacklistRule.objects.get(rule_id=1)
        existing = Watchlist.objects.get(email=email)
        diff = ts - existing.time
        
        # IF THE TIME DIFFERENCE IS LESS THAN BUFFER, INCREASE THE COUNTER
        if diff < BLACKLISTRULE.buffer_monitor:
            existing.counter += 1
            existing.time = ts
            existing.save()

            # IF THE COUNTER IS MORE THAN MAXIMUM
            if existing.counter > BLACKLISTRULE.max_counter:
                blacklist(email)
                existing.delete()

        # IF NOT, RESET THE COUNTER
        else:
            existing.counter = 1
            existing.time = ts
            existing.save()

        gerologger.info("Monitor Counter : "+str(existing.counter))

    else:
        watch = Watchlist()
        watch.email = email
        watch.time = ts
        watch.save()

# CLEAN WATCHLIST (SHOULD BE USED AS CRONJOB)
def clean():
    BLACKLISTRULE = BlacklistRule.objects.get(rule_id=1)
    watchlist = Watchlist.objects.all()
    ts = int(time.time())

    for watch in watchlist:
        diff = ts - watch.time
        if diff >= BLACKLISTRULE.buffer_clean:
            watch.delete()