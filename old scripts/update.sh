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
echo "BACKUP CURRENT FILES"
echo "=========================="
GEROBUG_DASHBOARD=$(docker container ls  | grep 'gerobug_dashboard' | awk '{print $1}')

if [[ $GEROBUG_DASHBOARD == "" ]]; then
    echo "No running Gerobug container found, use run.sh instead."
    exit 1
fi

rm gerobug_web/static/logo.png
rm gerobug_dashboard/static/logo.png
rm -rf gerobug_dashboard/static/templates

docker cp $GEROBUG_DASHBOARD:/src/static/logo.png gerobug_web/static/logo.png
docker cp $GEROBUG_DASHBOARD:/src/static/logo.png gerobug_dashboard/static/logo.png
docker cp $GEROBUG_DASHBOARD:/src/static/templates gerobug_dashboard/static/templates
docker cp $GEROBUG_DASHBOARD:/src/report_files gerobug_dashboard

sleep 3


echo -e "\n=========================="
echo "STOPPING CURRENT PROCESS"
echo "=========================="
docker-compose down
docker volume rm gerobug_static-content
sleep 3

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