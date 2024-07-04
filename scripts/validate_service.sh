#!/bin/bash

# Check if Django server is running
if pgrep -f "python3 manage.py runserver 0.0.0.0:8000" > /dev/null
then
     echo "Django server is running"
else
     echo "Django server is not running"
     exit 1
fi

# Check if Celery worker is running
if pgrep -f "celery -A home worker" > /dev/null
then
     echo "Celery worker is running"
else
     echo "Celery worker is not running"
     exit 1
fi