from django.db import models

# Create your models here.
class Position(models.Model):
     id = models.AutoField(primary_key=True)
     name = models.CharField(max_length=20, unique=True)
     total_cnt = models.IntegerField(default=0)
     recent_cnt = models.IntegerField(default=0)

     def __str__(self):
          return self.name
