from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from activity.models import *
from region.models import *
from position.models import *
from user.models import *

# Create your models here.
class Team(models.Model):
     id = models.AutoField(primary_key=True)
     name = models.CharField(max_length=20)
     short_pr = models.CharField(max_length=50)
     keywords = models.CharField(default='')
     activity = models.ForeignKey(Activity, 
                                   on_delete=models.CASCADE, 
                                   related_name='team',
                                   default=1
                                   )
     cities = models.ManyToManyField(
          City,
          related_name='team',
     )
     meet_preference = models.PositiveSmallIntegerField(
          validators=[
               MinValueValidator(0), 
               MaxValueValidator(100)
          ]
     )
     long_pr = models.TextField(default='')
     active_startdate = models.CharField(max_length=8, default='19000101')
     active_enddate = models.CharField(max_length=8, default='19000102')
     positions = models.ManyToManyField(
          Position,
          through="TeamPositions",
          related_name="teams",
     )
     recruit_startdate = models.CharField(max_length=8, default='19000101')
     recruit_enddate = models.CharField(max_length=8, default='19000101')
     members = models.ManyToManyField(
          User,
          through="TeamMembers",
          related_name="teams"
     )
     
     @property
     def member_cnt(self):
          return self.members.count()
     

class TeamPositions(models.Model):
     team = models.ForeignKey(Team, on_delete=models.CASCADE)
     position = models.ForeignKey(Position, on_delete=models.CASCADE)
     pr = models.CharField(default='', blank=True)
     cnt = models.PositiveSmallIntegerField(
          validators=[
               MinValueValidator(0), 
               MaxValueValidator(3000)
          ]
     )
     
     
class TeamMembers(models.Model):
     team = models.ForeignKey(Team, on_delete=models.CASCADE)
     user = models.ForeignKey(User, on_delete=models.CASCADE)
     position = models.ForeignKey(Position, on_delete=models.CASCADE, default=1)
     background = models.CharField(default='')
     avatar = models.CharField(default='')
     
     