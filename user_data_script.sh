#!/bin/bash
# Log the start of the user data script
echo "Starting user data script" > /var/log/user-data.log
cd /home/ubuntu/Teamit-django-backend-1/

# Update package lists and install necessary packages
apt-get update -y >> /var/log/user-data.log 2>&1
apt-get upgrade -y >> /var/log/user-data.log 2>&1
apt-get install -y python3-pip >> /var/log/user-data.log 2>&1


# activate virtual environment
python3 -m venv venv
source venv/bin/activate

cd /home/ubuntu/Teamit-django-backend-1/backend >> /var/log/user-data.log 2>&1

# install requirements.txt
pip install -r /home/ubuntu/Teamit-django-backend-1/requirements.txt >> /var/log/user-data.log 2>&1

# run database migrations
python3 manage.py migrate >> /var/log/user-data.log 2>&1

# run servers
nohup celery -A home worker --loglevel=info > nohup-celery.out 2>&1  &
nohup gunicorn -k uvicorn.workers.UvicornWorker home.asgi:application --reload --bind 0.0.0.0:2000 > gunicorn.log 2>&1 &

# Log user data script completion
echo "User data script completed" >> /var/log/user-data.log