web: DJANGO_SETTINGS_MODULE=core.settings gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 4
release: DJANGO_SETTINGS_MODULE=core.settings python manage.py migrate --noinput
