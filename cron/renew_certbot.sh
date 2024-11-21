#!/bin/bash

docker run --rm -p 8888:80 --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  -v "/var/www/letsencrypt:/var/www/letsencrypt" \
  certbot/certbot renew --webroot -w /var/www/letsencrypt --agree-tos

# Reload Nginx to apply new certificates (optional)
# docker exec gerobug_nginx nginx -s reload

# ADD CRON
# echo "0 2 1 * * /path/to/gerobug/cron/renew_certbot.sh >> /gerobug/log/renew_certbot.log 2>&1" | sudo crontab -

# DELETE CRON
# sudo crontab -l | grep -v "/gerobug/cron/renew_certbot.sh" | sudo crontab -
