release: /usr/bin/python3 manage.py migrate --noinput
web: gunicorn rag_system.wsgi:application --bind 0.0.0.0:$PORT --log-file -
