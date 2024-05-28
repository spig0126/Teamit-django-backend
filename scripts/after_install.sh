# kill any servers that may be running in the background 
sudo pkill -f runserver

cd /home/ubuntu/Teamit-django-backend-1/

# activate virtual environment
python3 -m venv venv
source venv/bin/activate

# # install requirements.txt
# pip install -r /home/ubuntu/acc-cicd-hands-on/requirements.txt

# run server
screen -d -m python3 manage.py runserver 0.0.0.0:8000 --settings=djangoProject.settings.prod

