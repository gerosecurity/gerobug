#!/bin/bash

echo "[LOG] Waiting for Database Initialization"
sleep 15

# Making migrations
echo "[LOG] Making migrations"
python manage.py makemigrations prerequisites
python manage.py makemigrations dashboards


# Migrating the database
echo "[LOG] Migrating the database"
MAX_RETRIES=5
RETRY_COUNT=0
until python manage.py migrate || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo "[LOG] Migration attempt $((RETRY_COUNT+1)) failed. Retrying..."
  RETRY_COUNT=$((RETRY_COUNT+1))
  sleep 3
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "[ERROR] Failed to migrate the database after $MAX_RETRIES attempts."
  exit 1
fi

# Creating Superuser if not exists
echo "[LOG] Creating Superuser "geromin""
if python manage.py shell -c "from django.contrib.auth.models import User; exit(User.objects.filter(username='geromin').exists())"; then
    echo "[LOG] Superuser 'geromin' already exists. Skipping creation."
else
    python manage.py createsuperuser --noinput --username "geromin" --email "geromin@localhost"
fi
echo '[LOG] "geromin" Password --> gerobug_dashboard/secrets/gerobug_secret.env'

# Collecting static files
echo "[LOG] Collecting static files"
python manage.py collectstatic --noinput --verbosity 1 | grep -v "It will be ignored"

echo "[LOG] GEROBUG-DASHBOARD is fully configured successfully."

# Execute the CMD passed to the container
exec "$@"
