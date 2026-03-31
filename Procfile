web: python manage.py migrate && daphne -b 0.0.0.0 -p ${PORT:-8000} --workers 1 core.asgi:application
