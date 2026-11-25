import time
import logging
from dashboards.models import Blacklist, Watchlist, BlacklistRule



# DEFAULT RULE ==> IF THERE ARE MORE THAN 10 EMAILS WITH <= 1 MINUTE INTERVAL, BLACKLIST FOR 1 HOUR
# MAX COUNTER BEFORE BLACKLIST (DEFAULT 10)
# BUFFER FOR COUNTER INTERVALS (DEFAULT 60 SECONDS)
# BUFFER FOR BLACKLIST PERIOD (DEFAULT 3600 SECONDS / 1 HOUR)
# BUFFER FOR CLEANING WATCHLIST (DEFAULT 86400 SECONDS / 24 HOUR)



def _key(email):
    return str(email or "").strip().lower()


_BOUNCE_ALERTS = {}
BOUNCE_ALERT_COOLDOWN = 3600


def bounce_alert_allowed(report_id):
    now = int(time.time())
    last = _BOUNCE_ALERTS.get(report_id)
    if last is not None and now - last < BOUNCE_ALERT_COOLDOWN:
        return False
    _BOUNCE_ALERTS[report_id] = now
    return True


# BLACKLIST SPAM EMAIL
def check_blacklist(email):
    email = _key(email)
    if Blacklist.objects.filter(email=email).exists():
        BLACKLISTRULE = BlacklistRule.objects.get(rule_id=1)
        blacklisted = Blacklist.objects.get(email=email)
        ct = int(time.time())
        diff =  ct - blacklisted.time 
    
        if diff < BLACKLISTRULE.buffer_blacklist:
            remaining = (blacklisted.time + BLACKLISTRULE.buffer_blacklist) - ct
            logging.getLogger("Gerologger").warning("Email Blacklisted Due to Spam Activity (Release in "+str(remaining)+" seconds)")
            logging.getLogger("Gerologger").info('============================')

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
            logging.getLogger("Gerologger").info("Email Released from Blacklist")
            return False, "", False
    
    else:
        return False, "", False

# BLACKLIST SPAM EMAIL
def blacklist(email):
    email = _key(email)
    black = Blacklist()
    black.email = email
    black.time = int(time.time())
    black.save()

# MONITOR SUSPECT EMAIL
def monitor(email, ts):
    email = _key(email)
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

        logging.getLogger("Gerologger").info("Monitor Counter : "+str(existing.counter))

    else:
        watch = Watchlist()
        watch.email = email
        watch.time = ts
        watch.save()