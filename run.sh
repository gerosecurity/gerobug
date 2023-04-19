#!/bin/bash

if [ ! -f ./secrets/ ]; then
    echo '[INFO] Creating Secret Folder...'
    mkdir secrets
fi

if [ ! -f ./secrets/db_secret.env ]; then
    echo '[INFO] Creating DB Secret...'
    echo 'POSTGRES_PASSWORD="'$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)'"' > ./secrets/db_secret.env    
fi

if [ ! -f ./secrets/gerobug_secret.env ]; then
    echo '[INFO] Creating Dashboard Secret...'
    DJANGO_SUPERUSER_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    export DJANGO_SUPERUSER_PASSWORD
    echo 'DJANGO_SUPERUSER_PASSWORD='$DJANGO_SUPERUSER_PASSWORD'"' > ./secrets/gerobug_secret.env
fi

docker-compose up