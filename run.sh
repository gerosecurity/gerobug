#!/bin/bash

echo "
 ______     ______     ______     ______     ______     __  __     ______    
/\  ___\   /\  ___\   /\  == \   /\  __ \   /\  == \   /\ \/\ \   /\  ___\   
\ \ \__ \  \ \  __\   \ \  __<   \ \ \/\ \  \ \  __<   \ \ \_\ \  \ \ \__ \  
 \ \_____\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_____\  \ \_____\  \ \_____\ 
  \/_____/   \/_____/   \/_/ /_/   \/_____/   \/_____/   \/_____/   \/_____/ 
                                                                             
"
echo "================================================================================"
echo "Gerobug v2.1 (PRODUCTION READY)"
echo "================================================================================"
echo ""
echo "================================================================================"

echo "---------------------------------"
echo "Welcome to the Gerobug Installer!"
echo "---------------------------------"
echo "My name is Gero and I will assist you through the installation :)"
echo "I need to ask you a few questions before starting the setup."
echo ""

# Detect public IPv4 address and pre-fill for the user
IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | head -1)
echo "Server Public IP : $IP"
echo $IP > ./gerobug_dashboard/gerobug_host
echo ""

IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | head -2 | tail -1)
echo "Server Internal IP : $IP"
echo $IP >> ./gerobug_dashboard/gerobug_host
echo ""

echo "Do you have a domain that you want to use?"
echo "example: demo.gerobug.com"
echo "   1) YES (I will help to implement HTTPS using lets encrypt for you)"
echo "   2) NO  (Gerobug will use HTTP instead of HTTPS) [NOT RECOMMENDED FOR PRODUCTION]"
until [[ $HAVE_DOMAIN =~ ^[1-2]$ ]]; do
    read -rp "Your choice [1-2]: " -e HAVE_DOMAIN
done
case $HAVE_DOMAIN in
1)
    DOMAIN="Y"
    ;;
2)
    DOMAIN="N"
    ;;
esac
echo ""

if [[ $DOMAIN == "Y" ]]; then
    #while [[ VALIDATE DOMAIN ]]; do
        read -p "Enter your domain (example: www.gerobug.com): " GEROBUG_HOST
    #done
    echo $GEROBUG_HOST >> ./gerobug_dashboard/gerobug_host
fi


echo "Do you have a VPN Server on the network?"
echo "   1) YES (Gerobug Dashboard will only accept connection from internal IP)"
echo "   2) NO  (Gerobug Dashboard will be accessible from public) [NOT RECOMMENDED FOR PRODUCTION]"
until [[ $HAVE_VPN =~ ^[1-2]$ ]]; do
    read -rp "Your choice [1-2]: " -e HAVE_VPN
done
case $HAVE_VPN in
1)
    VPN="Y"
    ;;
2)
    VPN="N"
    ;;
esac
echo ""

if [[ $VPN == "Y" ]]; then
    echo "OK, You have a VPN Server"
fi

echo "Okay, that was all I needed. We are ready to setup Gerobug server now."
read -n1 -r -p "Press any key to continue..."
echo -e "================================================================================\n"


echo -e "\n================================"
echo "CHECK AND INSTALL PREREQUISITES"
echo "================================"
apt-get install -y python3 docker docker.io docker-compose libmagic-dev
systemctl restart docker


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


echo -e "\n=============================="
echo "VIEWING GEROBUG LOG"
echo "=============================="

echo "(To Exit The Log Viewer, Use Ctrl + C)"
docker-compose logs -f