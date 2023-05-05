#!/bin/bash

echo "
 ______     ______     ______     ______     ______     __  __     ______    
/\  ___\   /\  ___\   /\  == \   /\  __ \   /\  == \   /\ \/\ \   /\  ___\   
\ \ \__ \  \ \  __\   \ \  __<   \ \ \/\ \  \ \  __<   \ \ \_\ \  \ \ \__ \  
 \ \_____\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_____\  \ \_____\  \ \_____\ 
  \/_____/   \/_____/   \/_/ /_/   \/_____/   \/_____/   \/_____/   \/_____/ 
                                                                             
"

echo "================================================================================"
echo "Gerobug Dashboard should only be accessible internally to avoid security risks"
echo "[IT IS RECOMMENDED TO SET ALLOWED HOST USING STATIC INTERNAL IP]"
echo -e "================================================================================\n"

echo "IP Address: " 
echo $(ip addr | grep inet)

echo -e "\n=========================="
echo "GEROBUG DASHBOARD IP SETUP"
echo "=========================="

if [ ! -f ./gerobug_dashboard/gerobug_host ]; then
    rx='([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    while [[ ! $IP =~ ^$rx\.$rx\.$rx\.$rx$ ]]; do
        echo "Provide Static IP for Gerobug Dashboard (Internal Static IP):"
        read IP
        echo
    done
    echo $IP > ./gerobug_dashboard/gerobug_host
else
    echo "Current Allowed Host: $(<./gerobug_dashboard/gerobug_host)"
    echo -e "[* IS NOT RECOMMENDED, CHANGE TO STATIC INTERNAL IP]\n"
    ANSWER=""

    select RESULT in 'Change IP' 'Continue with Current Allowed Host'; do
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
        echo $IP > ./gerobug_dashboard/gerobug_host
    fi
fi

echo -e "\n================================"
echo "CHECK AND INSTALL PREREQUISITES"
echo "================================"
apt-get install -y python3 docker docker.io docker-compose


echo -e "\n=============================="
echo "CREATE SECRET FILES"
echo "=============================="

if [ ! -d ./gerobug_dashboard/secrets ]; then
    echo '[LOG] Creating New Secret Folder...'
    mkdir ./gerobug_dashboard/secrets
    mkdir ./gerobug_web/secrets
fi

if [ ! -f ./gerobug_dashboard/secrets/db_secret.env ]; then
    echo '[LOG] Creating New DB Secret...'
    echo 'POSTGRES_PASSWORD="'$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)'"' > ./gerobug_dashboard/secrets/db_secret.env 
    cp  ./gerobug_dashboard/secrets/db_secret.env ./gerobug_web/secrets/db_secret.env 
fi

if [ ! -f ./gerobug_dashboard/secrets/gerobug_secret.env ]; then
    echo '[LOG] Creating New Gerobug Secret...'
    DJANGO_SUPERUSER_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    export DJANGO_SUPERUSER_PASSWORD
    echo 'DJANGO_SUPERUSER_PASSWORD="'$DJANGO_SUPERUSER_PASSWORD'"' > ./gerobug_dashboard/secrets/gerobug_secret.env
fi

echo -e "\n=============================="
echo "BUILDING GEROBUG"
echo "=============================="

docker-compose up --build --force-recreate -d
