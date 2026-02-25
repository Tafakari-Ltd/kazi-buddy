#!/bin/bash

set -e

# Navigate to the Django project directory
cd /app/tafakari

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting application..."
exec "$@"
