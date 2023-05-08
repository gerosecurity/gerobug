#!/bin/bash

echo "
 ______     ______     ______     ______     ______     __  __     ______    
/\  ___\   /\  ___\   /\  == \   /\  __ \   /\  == \   /\ \/\ \   /\  ___\   
\ \ \__ \  \ \  __\   \ \  __<   \ \ \/\ \  \ \  __<   \ \ \_\ \  \ \ \__ \  
 \ \_____\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_____\  \ \_____\  \ \_____\ 
  \/_____/   \/_____/   \/_/ /_/   \/_____/   \/_____/   \/_____/   \/_____/ 
                                                                             
"

echo "================================================================================"
echo "Gerobug v1.1 (Monolith Architecture)"
echo "NOT READY FOR PRODUCTION USE!"
echo -e "================================================================================\n"


echo -e "\n================================"
echo "CHECK AND INSTALL PREREQUISITES"
echo "================================"
apt-get install -y python3 docker docker.io docker-compose libmagic-dev
systemctl restart docker


echo -e "\n=============================="
echo "BUILDING GEROBUG"
echo "=============================="

docker-compose up --build --force-recreate -d


echo -e "\n=============================="
echo "VIEWING GEROBUG LOG"
echo "=============================="

docker-compose logs -f