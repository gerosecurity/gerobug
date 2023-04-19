#!/bin/bash

if [ ! -f ./db_secret.env ]; then
    echo '[INFO] Creating DB Secret...'
    echo 'POSTGRES_PASSWORD="'$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)'"' > db_secret.env    
fi

if [ ! -f ./gerobug_secret ]; then
    echo '[INFO] Creating Dashboard Secret...'
    DJANGO_SUPERUSER_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    echo $DJANGO_SUPERUSER_PASSWORD > gerobug_secret
    export DJANGO_SUPERUSER_PASSWORD
fi

docker-compose up