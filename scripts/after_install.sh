c#!/bin/bash

cd /home/ubuntu/Teamit-django-backend-1/

# activate virtual environment
python3 -m venv venv
source venv/bin/activate

cd /home/ubuntu/Teamit-django-backend-1/backend

# install requirements.txt
pip install -r /home/ubuntu/Teamit-django-backend-1/requirements.txt

# run database migrations
python3 manage.py migrate


