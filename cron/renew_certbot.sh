#!/bin/bash

docker run --rm -p 8888:80 --name certbot \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  -v "/var/www/letsencrypt:/var/www/letsencrypt" \
  certbot/certbot renew --non-interactive --agree-tos --webroot --webroot-path /var/www/letsencrypt

# Reload Nginx to apply new certificates
cd "$(dirname "$(readlink -f "$0")")/.." && docker compose exec -T nginx nginx -s reload || echo "Warning: Could not reload nginx. Please reload manually."

# ADD CRON
# echo "0 2 1 * * /path/to/gerobug/cron/renew_certbot.sh >> /gerobug/log/renew_certbot.log 2>&1" | sudo crontab -

# DELETE CRON
# To remove the cron job: sudo crontab -l | grep -v renew_certbot.sh | sudo crontab -
