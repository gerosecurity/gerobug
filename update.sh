echo "=========================="
echo "Gerobug Updater"
echo -e "==========================\n"

rx='(Y|N)'
while [[ ! $ANS =~ ^$rx$ ]]; do
    echo "Want to Update Gerobug? (Y/N)"
    read ANS
    echo
done

if [[ $ANS == "N" ]]; then
    echo "Good bye, have a good day."
    exit 1
fi
ANS=''

echo -e "\n=========================="
echo "PULL LATEST UPDATES"
echo "=========================="
git branch --set-upstream-to=origin/main
git pull
sleep 3

echo -e "\n=========================="
echo "STOPPING CURRENT PROCESS"
echo "=========================="
docker-compose down

while [[ ! $ANS =~ ^$rx$ ]]; do
    echo -e "\nUPDATE STATIC FILES?"
    echo "If Y, any updates on static files will be applied, but you need to re-upload your logo and templates after the update"
    echo "If N, Updates on static files will NOT be applied"
    echo "(Y/N)"
    read ANS
    echo
done

if [[ $ANS == "Y" ]]; then
    docker volume rm gerobug_static-content
    sleep 3
fi

echo -e "\n=========================="
echo "REBUILD UPDATES"
echo "=========================="
docker-compose up --build --force-recreate -d
sleep 3

echo -e "\n=============================="
echo "VIEWING GEROBUG LOG"
echo "=============================="

echo "(To Exit The Log Viewer, Use Ctrl + C)"
docker-compose logs -f