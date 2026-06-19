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

# Creating Superuser
echo "[LOG] Creating Superuser "geromin""
python manage.py createsuperuser --noinput --username "geromin" --email "geromin@localhost"
echo '[LOG] "geromin" Password --> gerobug_dashboard/secrets/gerobug_secret.env'

if [ -z "$FIELD_ENCRYPTION_KEY" ]; then
  echo "[LOG] Generating FIELD_ENCRYPTION_KEY..."
  FIELD_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  export FIELD_ENCRYPTION_KEY
  SECRET_FILE="/src/secrets/gerobug_secret.env"
  if [ -f "$SECRET_FILE" ]; then
    if ! grep -q "FIELD_ENCRYPTION_KEY" "$SECRET_FILE"; then
      echo "FIELD_ENCRYPTION_KEY=$FIELD_ENCRYPTION_KEY" >> "$SECRET_FILE"
      echo "[LOG] FIELD_ENCRYPTION_KEY written to gerobug_secret.env"
    fi
  fi
fi

echo "[LOG] Encrypting existing sensitive data..."
python manage.py encrypt_existing_data

# Collecting static files
echo "[LOG] Collecting static files"
python manage.py collectstatic --noinput --verbosity 1 | grep -v "It will be ignored"

echo "[LOG] GEROBUG-DASHBOARD is fully configured successfully."

# Execute the CMD passed to the container
exec "$@"
