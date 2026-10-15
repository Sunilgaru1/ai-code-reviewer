#!/bin/bash

# Apply database migrations first
python manage.py migrate

# Start Celery with the solo pool to use only one background process
celery -A config worker --loglevel=info --pool=solo &

# Start Gunicorn with exactly 1 worker to strictly limit web server memory usage
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1
