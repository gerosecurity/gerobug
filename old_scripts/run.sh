#!/bin/bash

echo "
 ______     ______     ______     ______     ______     __  __     ______    
/\  ___\   /\  ___\   /\  == \   /\  __ \   /\  == \   /\ \/\ \   /\  ___\   
\ \ \__ \  \ \  __\   \ \  __<   \ \ \/\ \  \ \  __<   \ \ \_\ \  \ \ \__ \  
 \ \_____\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_____\  \ \_____\  \ \_____\ 
  \/_____/   \/_____/   \/_/ /_/   \/_____/   \/_____/   \/_____/   \/_____/ 
                                                                             
"
echo "================================================================================"
echo "Gerobug v2.5 (PRODUCTION READY)"
echo "================================================================================"
echo ""
echo "================================================================================"

echo "---------------------------------"
echo "Welcome to the Gerobug Installer!"
echo "---------------------------------"
echo "My name is Gero and I will assist you through the installation :)"
echo "I need to ask you a few questions before starting the setup."
echo ""

# Detect Public IPv4
truncate -s 0 ./gerobug_dashboard/gerobug_host
IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | head -1)
echo "Server Public IP : $IP"
echo "Is it correct?"
echo "   1) YES"
echo "   2) NO"
until [[ $CHOICE =~ ^[1-2]$ ]]; do
    read -rp "Your choice [1-2]: " -e CHOICE
done
case $CHOICE in
1)
    CHOICE="Y"
    ;;
2)
    CHOICE="N"
    ;;
esac

if [[ $CHOICE == "Y" ]]; then
    echo $IP >> ./gerobug_dashboard/gerobug_host
else
    IP=''
    rx='([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    while [[ ! $IP =~ ^$rx\.$rx\.$rx\.$rx$ ]]; do
        read -p "Enter Public / Primary IP: " IP
    done
    echo $IP >> ./gerobug_dashboard/gerobug_host
fi
echo ""

# Detect Internal IPv4
IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | head -2 | tail -1)
echo "Server Internal IP : $IP"
echo "Is it correct?"
echo "   1) YES"
echo "   2) NO"
until [[ $CHOICE =~ ^[1-2]$ ]]; do
    read -rp "Your choice [1-2]: " -e CHOICE
done
case $CHOICE in
1)
    CHOICE="Y"
    ;;
2)
    CHOICE="N"
    ;;
esac

if [[ $CHOICE == "Y" ]]; then
    echo $IP >> ./gerobug_dashboard/gerobug_host
else
    IP=''
    rx='([1-9]?[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'
    while [[ ! $IP =~ ^$rx\.$rx\.$rx\.$rx$ ]]; do
        read -p "Enter Internal / Secondary IP (example: 127.0.0.1): " IP
    done
    echo $IP >> ./gerobug_dashboard/gerobug_host
fi
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

# CLEAR DEFAULT CONFIG
DEFAULT=./nginx/default.conf
if [[ -f "$DEFAULT" ]]; then
    rm ./nginx/default.conf
fi

RX='^([a-zA-Z0-9-]{1,61}[a-zA-Z0-9])\.([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30})\.([a-zA-Z]{2,8}(\.[a-zA-Z]{2,3})?)$'
if [[ $DOMAIN == "Y" ]]; then
    # READ DOMAIN
    while [[ ! "$GEROBUG_HOST" =~ $RX ]]; do
        read -p "Enter your domain (example: www.gerobug.com): " GEROBUG_HOST
    done
    echo $GEROBUG_HOST >> ./gerobug_dashboard/gerobug_host

    # CREATE CLEAN HTTPS CONFIG
    cp ./nginx/default.https.conf ./nginx/default.conf

    # REPLACE DOMAIN NAME
    sed -i "s/{\$DOMAIN}/$GEROBUG_HOST/g" ./nginx/default.conf

    # RUN CERTBOT
    echo -e "\n================================"
    echo "SETTING UP HTTPS"
    echo "================================"
    apt-get install -y docker docker.io
    docker run -it --rm -p 80:80 --name certbot \
    -v "/etc/letsencrypt:/etc/letsencrypt" \
    -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
    certbot/certbot certonly --standalone -d $GEROBUG_HOST
else
    echo "Gerobug will not implement HTTPS [NOT RECOMMENDED FOR PRODUCTION]"
    echo "A domain is required to setup HTTPS"
    echo ""
    echo "Run this script again later when you have a domain to setup HTTPS"
    echo "or you can change the nginx config manually"
    
    # CREATE CLEAN HTTP CONFIG
    cp ./nginx/default.http.conf ./nginx/default.conf
fi
echo ""


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

if [[ $VPN == "N" ]]; then
    echo "Gerobug Dashboard will be accessible from public connection"
    echo "[WARNING] THIS IS NOT RECOMMENDED FOR PRODUCTION SERVER!"
    sed -i '/^.*allow   .*/s/^/#/g' ./nginx/default.conf
    sed -i '/^.*deny   .*/s/^/#/g' ./nginx/default.conf
else
    echo "Gerobug Dashboard will only accept connection from INTERNAL IP"
    echo "So a VPN Server will be required"
    echo "If you face any trouble, read the documentation :)"
    sed -i '/^#.*allow   .*/s/^#//' ./nginx/default.conf
    sed -i '/^#.*deny   .*/s/^#//' ./nginx/default.conf
fi
echo ""

echo "Okay, that was all I needed. We are ready to setup Gerobug server now."
read -n1 -r -p "Press any key to continue..."
echo -e "================================================================================\n"


echo -e "\n================================"
echo "CHECK AND INSTALL PREREQUISITES"
echo "================================"
apt-get install -y python3 docker docker.io docker-compose libmagic-dev

extract_version() {
    echo "$1" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+'
}
CURRENT_COMPOSE_VERSION=$(extract_version "$(docker-compose --version)")
MIN_COMPOSE_VERSION="1.29.2"

if [ -z "$CURRENT_COMPOSE_VERSION" ]; then
    echo "Unable to determine docker-compose version."
    exit 1
fi

version_gt() { test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"; }
if version_gt $MIN_COMPOSE_VERSION $CURRENT_COMPOSE_VERSION; then
    echo "=============================="
    echo "Your docker-compose version ($CURRENT_COMPOSE_VERSION) is less than the minimum required version ($MIN_COMPOSE_VERSION)."
    echo -e "Updating Docker Compose...\n"

    DESTINATION=$(which docker-compose)
    sudo wget "https://github.com/docker/compose/releases/download/v2.24.2/docker-compose-$(uname -s)-$(uname -m)" -O $DESTINATION
    sudo chmod +x $DESTINATION

    UPDATED_COMPOSE_VERSION=$(extract_version "$(docker-compose --version)")
    echo "=============================="
    echo "Docker Compose has been updated to version $UPDATED_COMPOSE_VERSION."
else
    echo -e "\nYour docker-compose version ($CURRENT_COMPOSE_VERSION) meets the minimum required version ($MIN_COMPOSE_VERSION)."
fi

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
    POSTGRES_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    export POSTGRES_PASSWORD
    echo "POSTGRES_PASSWORD='$POSTGRES_PASSWORD'" > ./gerobug_dashboard/secrets/db_secret.env
    cp  ./gerobug_dashboard/secrets/db_secret.env ./gerobug_web/secrets/db_secret.env
fi

if [ ! -f ./gerobug_dashboard/secrets/gerobug_secret.env ]; then
    echo '[LOG] Creating New Gerobug Secret...'
    DJANGO_SUPERUSER_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    export DJANGO_SUPERUSER_PASSWORD
    echo "DJANGO_SUPERUSER_PASSWORD='$DJANGO_SUPERUSER_PASSWORD'" > ./gerobug_dashboard/secrets/gerobug_secret.env
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
