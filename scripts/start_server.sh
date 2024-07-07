#!/bin/bash

cd /home/ubuntu/Teamit-django-backend-1/backend

# run server
nohup python3 manage.py runserver 0.0.0.0:8000 & 
nohup celery -A home worker --loglevel=info > nohup-celery.out 2>&1  &
