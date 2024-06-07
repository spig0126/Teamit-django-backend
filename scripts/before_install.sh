
echo "clean codedeploy-agent files for a fresh install"
sudo rm -rf /home/ubuntu/install

echo "install CodeDeploy agent"
sudo apt-get -y update
sudo apt-get -y install ruby
sudo apt-get -y install wget
cd /home/ubuntu
wget https://aws-codedeploy-us-east-1.s3.amazonaws.com/latest/install
sudo chmod +x ./install 
sudo ./install auto

echo "update os & install python3"
sudo apt-get update
sudo apt-get install -y python3 python3-dev python3-pip python3-venv
pip install --user --upgrade virtualenv

# Find the PID of the Python process
PID=$(ps aux | grep '[p]ython3 manage.py runserver 0.0.0.0:8000' | awk '{print $2}')

# Check if PID is not empty
if [ -n "$PID" ]; then
     echo "Stopping Django server with PID $PID"
     kill $PID
else
     echo "Python server is not running"
fi

# Find the PID of the Celery worker process
PID=$(ps aux | grep '[c]elery -A home worker' | awk '{print $2}')

# Check if PID is not empty
if [ -n "$PID" ]; then
     echo "Stopping Celery worker with PID $PID"
     kill $PID
else
     echo "Celery worker is not running"
fi

echo "delete app"
sudo rm -rf /home/ubuntu/Teamit-django-backend-1