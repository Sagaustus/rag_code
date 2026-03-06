release: python manage.py migrate --noinput
web: gunicorn rag_system.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --log-file -
