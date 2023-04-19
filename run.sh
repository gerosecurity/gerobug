#!/bin/bash

if [ ! -f ./db_secret.env ]; then
    echo '[INFO] Creating DB Secret...'
    echo 'POSTGRES_PASSWORD="'$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)'"' > db_secret.env    
fi

docker-compose up