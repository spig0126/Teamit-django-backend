cd /home/ubuntu/Teamit-django-backend-1/

# activate virtual environment
python3 -m venv venv
source venv/bin/activate

# install requirements.txt
pip install -r /home/ubuntu/Teamit-django-backend-1/requirements.txt

# run server
nohup python3 manage.py runserver 0.0.0.0:8000 & 
nohup celery -A home worker --loglevel=info > nohup-celery.out 2>&1  &

