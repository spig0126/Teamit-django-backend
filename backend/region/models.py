from django.db import models
from django.utils.text import slugify

# Create your models here.
class Province(models.Model):
     name = models.CharField(max_length=2, unique=True)

     def __str__(self):
          return self.name


class City(models.Model):
     name = models.CharField(max_length=10)
     province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities')
     full_name = models.CharField(max_length=20, blank=True, default='')
     
     def __str__(self):
          return f"{self.province.name} {self.name}"
