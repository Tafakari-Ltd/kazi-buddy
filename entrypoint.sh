#!/bin/bash

set -e

echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h db -p 5432 -U ${DB_USER:-kazibuddy_user} > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - continuing..."

# Navigate to the Django project directory
cd /app/tafakari

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (optional)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py shell << END
from accounts.models import CustomUser
if not CustomUser.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    CustomUser.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        full_name='$DJANGO_SUPERUSER_USERNAME',
        phone_number=None,
        user_type='employer'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
END
fi

echo "Starting application..."
exec "$@"
