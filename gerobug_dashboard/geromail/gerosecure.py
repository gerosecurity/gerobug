import time

from dashboards.models import Blacklist, Watchlist



# DEFAULT RULE ==> IF THERE ARE MORE THAN 10 EMAILS WITH <= 1 MINUTE INTERVAL, BLACKLIST FOR 1 HOUR

# MAX COUNTER BEFORE BLACKLIST
MAX_COUNTER = 10

# BUFFER FOR COUNTER INTERVALS (DEFAULT 60 SECONDS)
BUFFER_MONITOR = 60 #SECONDS

# BUFFER FOR BLACKLIST PERIOD (DEFAULT 3600 SECONDS / 1 HOUR)
BUFFER_BLACKLIST = 3600 #SECONDS

# BUFFER FOR CLEANING WATCHLIST (DEFAULT 86400 SECONDS / 24 HOUR)
BUFFER_CLEAN = 86400 #SECONDS



# BLACKLIST SPAM EMAIL
def check_blacklist(email):
    if Blacklist.objects.filter(email=email).exists():
        blacklisted = Blacklist.objects.get(email=email)
        ct = int(time.time())
        diff =  ct - blacklisted.time 
    
        if diff < BUFFER_BLACKLIST:
            remaining = (blacklisted.time + BUFFER_BLACKLIST) - ct
            print("[LOG] Email Blacklisted Due to Spam Activity (Release in",remaining,"seconds)")
            print('============================\n')

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
            print("[LOG] Email Released from Blacklist")
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
        existing = Watchlist.objects.get(email=email)
        diff = ts - existing.time
        
        # IF THE TIME DIFFERENCE IS LESS THAN BUFFER, INCREASE THE COUNTER
        if diff < BUFFER_MONITOR:
            existing.counter += 1
            existing.time = ts
            existing.save()

            # IF THE COUNTER IS MORE THAN MAXIMUM
            if existing.counter > MAX_COUNTER:
                blacklist(email)
                existing.delete()

        # IF NOT, RESET THE COUNTER
        else:
            existing.counter = 0
            existing.time = ts
            existing.save()

        print("Monitor Counter :", existing.counter)

    else:
        watch = Watchlist()
        watch.email = email
        watch.time = ts
        watch.save()

# CLEAN WATCHLIST (SHOULD BE USED AS CRONJOB)
def clean():
    watchlist = Watchlist.objects.all()
    ts = int(time.time())

    for watch in watchlist:
        diff = ts - watch.time
        if diff >= BUFFER_CLEAN:
            watch.delete()