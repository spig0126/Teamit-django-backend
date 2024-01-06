from django.db import models

class Interest(models.Model):
     id = models.AutoField(primary_key=True)
     name = models.CharField(max_length=10, unique=True)
     total_cnt = models.IntegerField(default=0)
     recent_cnt = models.IntegerField(default=0)

     def __str__(self):
          return self.name