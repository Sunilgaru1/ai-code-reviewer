#!/bin/bash

# Apply database migrations first
python manage.py migrate

# Start the Celery worker in the background (using the & symbol)
celery -A config worker --loglevel=info &

# Start the Django web server using Gunicorn (best for production)
gunicorn config.wsgi:application --bind 0.0.0.0:8000