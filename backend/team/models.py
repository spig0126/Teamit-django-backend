from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import *

from activity.models import *
from region.models import *
from position.models import *
from user.models import *

# Create your models here.
class Team(models.Model):
     id = models.AutoField(primary_key=True)
     creator = models.ForeignKey(User, on_delete=models.CASCADE, default=54)
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
     active_startdate = models.CharField(max_length=10, default='1900-01-01')
     active_enddate = models.CharField(max_length=10, default='1900-01-02')
     positions = models.ManyToManyField(
          Position,
          through="TeamPositions",
          related_name="teams",
     )
     recruit_startdate = models.CharField(max_length=10, default='1900-01-01')
     recruit_enddate = models.CharField(max_length=10, default='1900-01-01')
     members = models.ManyToManyField(
          User,
          through="TeamMembers",
          related_name="teams"
     )
     image = models.CharField(default='')
     
     def __str__(self):
          return self.name
     
     @property
     def member_cnt(self):
          return self.members.count()
          
     @property
     def date_status(self):
          today = date.today()
          recruit_startdate = date.fromisoformat(self.recruit_startdate)
          recruit_enddate = date.fromisoformat(self.recruit_enddate)
          active_enddate = date.fromisoformat(self.active_enddate)
          
          if (recruit_startdate - today).days >= 0:
               return "모집예정"
          elif (recruit_enddate - today).days < 0:
               print((recruit_enddate - today).days)
               return "모집완료"
          elif (active_enddate - today).days <= 0:
               return "활동종료"
          else:
               return "D" + str((today - recruit_enddate).days)
     

class TeamPositions(models.Model):
     id = models.AutoField(primary_key=True)
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

class TeamApplication(models.Model):
     team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='applications')
     applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications') 
     position = models.ForeignKey(Position, on_delete=models.CASCADE)
     accepted = models.BooleanField(null=True, default=None)
     
     def save(self, *args, **kwargs):
          is_new = self.pk is None
          super().save(*args, **kwargs)
          
          if is_new:
               from notification.models import TeamNotification
               
               TeamNotification.objects.create(
                    type="team_application",
                    to_team = self.team,
                    related = self
               )
     