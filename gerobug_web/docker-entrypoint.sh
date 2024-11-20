#!/bin/bash


sleep 60

echo "[LOG] Making migrations ..."
while ! python manage.py makemigrations dashboards 2>&1; do
  echo "[LOG] Made migrations"
  sleep 3
done

echo "[LOG] Migrate the Database ..."
while ! python manage.py migrate 2>&1; do
   echo "[LOG] Migration is in progress status 0"
   sleep 3
done

while ! python manage.py migrate dashboards 2>&1; do
   echo "[LOG] Migration is in progress status 1"
   sleep 3
done

echo "[LOG] GEROBUG-WEB is fully configured successfully."

exec "$@"
