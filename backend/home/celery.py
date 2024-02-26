import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'home.settings')

app = Celery('home')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Use Redis as the broker
app.conf.broker_url = 'redis://localhost:6379/0'

# Optionally, specify the Redis backend for result storage
app.conf.result_backend = 'redis://localhost:6379/0'

# Automatically discover tasks in your installed apps
app.autodiscover_tasks()
