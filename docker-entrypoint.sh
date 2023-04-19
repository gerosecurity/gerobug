#!/bin/bash

echo "[LOG] Waiting 60s for Database Initialization..."
sleep 60

echo "[LOG] Making migrations ..."
while ! python manage.py makemigrations dashboards 2>&1; do
  echo "[LOG] Made migrations to Dashboard's Models"
  sleep 3
done

while ! python manage.py makemigrations prerequisites 2>&1; do
  echo "[LOG] Made migrations to Prerequisite's Models"
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

while ! python manage.py migrate prerequisites 2>&1; do
   echo "[LOG] Migration is in progress status 2"
   sleep 3
done

echo "[LOG] Creating Superuser "geromin" with password: "$DJANGO_SUPERUSER_PASSWORD
python manage.py createsuperuser --noinput --username "geromin" --email "geromin@localhost"

python manage.py collectstatic --noinput

echo "[LOG] Django docker is fully configured successfully."

exec "$@"
