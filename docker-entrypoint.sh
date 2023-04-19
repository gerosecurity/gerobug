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
while ! python manage.py migrate 2>&1; do
   echo "Migration is in progress status 0"
   sleep 3
done

while ! python manage.py migrate dashboards 2>&1; do
   echo "Migration is in progress status 1"
   sleep 3
done

while ! python manage.py migrate prerequisites 2>&1; do
   echo "Migration is in progress status 2"
   sleep 3
done

echo "Creating Superuser "geromin" with password="$DOCKER_SUPERUSER_PASSWORD
python manage.py createsuperuser --noinput --username "geromin" --email "geromin@localhost"

python manage.py collectstatic --noinput

echo "Django docker is fully configured successfully."

exec "$@"
