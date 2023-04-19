#!/bin/bash

echo "IP Address: " $(ip addr | grep inet)

echo "=============================="

if [ ! -f ./gerobug_host ]; then
    rx='([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    while [[ ! $IP =~ ^$rx\.$rx\.$rx\.$rx$ ]]; do
        echo "Provide Static IP for Gerobug Dashboard (Internal Static IP):"
        read IP
        echo
    done
    echo $IP > ./gerobug_host
else
    echo "Previous IP Detected:" $(cat ./gerobug_host)
    ANSWER=""

    select RESULT in 'Continue' 'Change IP'; do
        case $REPLY in
            [12])
                break
                ;;
            *)
                echo 'Invalid Input' >&2
        esac
    done
    
    if [[ $RESULT == "Change IP" ]]; then
        rx='([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
        while [[ ! $IP =~ ^$rx\.$rx\.$rx\.$rx$ ]]; do
            echo "Provide Static IP for Gerobug Dashboard (Internal Static IP):"
            read IP
            echo
        done
        echo $IP > ./gerobug_host
    fi
fi

echo "=============================="

if [ ! -d ./secrets ]; then
    echo '[LOG] Creating New Secret Folder...'
    mkdir secrets
fi

if [ ! -f ./secrets/db_secret.env ]; then
    echo '[LOG] Creating New DB Secret...'
    echo 'POSTGRES_PASSWORD="'$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)'"' > ./secrets/db_secret.env    
fi

if [ ! -f ./secrets/gerobug_secret.env ]; then
    echo '[LOG] Creating New Gerobug Secret...'
    DJANGO_SUPERUSER_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    export DJANGO_SUPERUSER_PASSWORD
    echo 'DJANGO_SUPERUSER_PASSWORD="'$DJANGO_SUPERUSER_PASSWORD'"' > ./secrets/gerobug_secret.env
fi

echo "=============================="

docker-compose up --build --force-recreate -d