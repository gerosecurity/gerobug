#!/bin/bash

echo "Making migrations ..."

while ! python manage.py makemigrations dashboards 2>&1; do
  echo "Made migrations to Dashboard's Models"
  sleep 3
done

while ! python manage.py makemigrations prerequisites 2>&1; do
  echo "Made migrations to Prerequisite's Models"
  sleep 3
done


echo "Migrate the Database ..."

# Wait for few minute and run db migration
while ! python manage.py migrate dashboards 2>&1; do
   echo "Migration is in progress status 1"
   sleep 3
done

while ! python manage.py migrate prerequisites 2>&1; do
   echo "Migration is in progress status 2"
   sleep 3
done

python manage.py collectstatic --noinput

if [ ! -f ./gerobug_secret ]; then
    echo '[INFO] Creating Dashboard Secret...'
    DJANGO_SUPERUSER_PASSWORD=$(tr -dc 'A-Za-z0-9!#$%&*?@' </dev/urandom | head -c 30)
    echo $DJANGO_SUPERUSER_PASSWORD > gerobug_secret
    export DJANGO_SUPERUSER_PASSWORD
fi

python manage.py createsuperuser --noinput --username "geromin" --email "geromin@localhost"

echo "Django docker is fully configured successfully."

exec "$@"
