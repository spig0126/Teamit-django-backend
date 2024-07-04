#!/bin/bash

# Stop the Django server
PID=$(ps aux | grep '[p]ython3 manage.py runserver 0.0.0.0:8000' | awk '{print $2}')
if [ -n "$PID" ]; then
     echo "Stopping Django server with PID $PID"
     kill $PID
else
     echo "Python server is not running"
fi

# Stop the Celery worker
PID=$(ps aux | grep '[c]elery -A home worker' | awk '{print $2}')
if [ -n "$PID" ]; then
     echo "Stopping Celery worker with PID $PID"
     kill $PID
else
     echo "Celery worker is not running"
fi

# Delete app
echo "delete app"
sudo rm -rf /home/ubuntu/Teamit-django-backend-1