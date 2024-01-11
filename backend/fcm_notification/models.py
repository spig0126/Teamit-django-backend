from django.db import models

from user.models import User

class Device(models.Model):
     id = models.AutoField(primary_key=True)
     user = models.ForeignKey(User, on_delete=models.CASCADE)
     token = models.CharField()
     timestamp = models.DateTimeField(auto_now=True)
     