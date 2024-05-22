echo "=========================="
echo "Gerobug SSL Renew"
echo -e "==========================\n"

rx='(Y|N)'
while [[ ! $ANS =~ ^$rx$ ]]; do
    echo "Want to Renew Gerobug SSL Certificate? (Y/N)"
    read ANS
    echo
done

if [[ $ANS == "N" ]]; then
    echo "Good bye, have a good day."
    exit 1
fi

docker run -it --rm -p 8888:80 --name certbot \
    -v "/etc/letsencrypt:/etc/letsencrypt" \
    -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
    certbot/certbot certonly --standalone -d $(tail -n 1 gerobug_dashboard/gerobug_host)