echo "=========================="
echo "Gerobug Restarter"
echo -e "==========================\n"

rx='(Y|N)'
while [[ ! $ANS =~ ^$rx$ ]]; do
    echo "Want to Restart Gerobug? (Y/N)"
    read ANS
    echo
done

if [[ $ANS == "N" ]]; then
    echo "Good bye, have a good day."
    exit 1
fi

echo -e "\n=========================="
echo "STOPPING CURRENT PROCESS"
echo "=========================="
docker compose down
sleep 1

echo -e "\n=========================="
echo "REBUILD UPDATES"
echo "=========================="
docker compose up --build --force-recreate -d
sleep 1

echo -e "\n=============================="
echo "VIEWING GEROBUG LOG"
echo "=============================="

echo "(To Exit The Log Viewer, Use Ctrl + C)"
docker compose logs -f