from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import *

from activity.models import *
from region.models import *
from position.models import *
from user.models import *
from fcm_notification.utils import send_fcm_to_team

class Team(models.Model):
     id = models.AutoField(primary_key=True)
     creator = models.ForeignKey(User, on_delete=models.CASCADE, default=54, related_name='created_teams')
     name = models.CharField(max_length=20)
     short_pr = models.CharField(max_length=50)
     keywords = models.CharField(default='')
     image = models.ImageField(upload_to='teams/', default='teams/default.png', null=True)
     
     activity = models.ForeignKey(Activity, 
                                   on_delete=models.CASCADE, 
                                   related_name='team',
                                   default=1
                                   )
     interest = models.ForeignKey(Interest, 
                                   on_delete=models.CASCADE,
                                   related_name='interest',
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
     active_startdate = models.CharField(max_length=10, default='2024-01-01')
     active_enddate = models.CharField(max_length=10, default='2024-01-02')
     positions = models.ManyToManyField(
          Position,
          through="TeamPositions",
          related_name="teams",
     )
     recruit_startdate = models.CharField(max_length=10, default='2024-01-01')
     recruit_enddate = models.CharField(max_length=10, default='2024-01-02')
     members = models.ManyToManyField(
          User,
          through="TeamMembers",
          related_name="teams"
     )
     
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
          
          recruiting_positions = len(self.positions.all())
          if (recruit_startdate - today).days >= 0:
               return "모집예정"
          elif (recruit_enddate - today).days < 0 or not recruiting_positions:
               return "모집완료"
          elif (recruit_enddate - today).days == 0:
               return "오늘 마감"
          elif (active_enddate - today).days <= 0:
               return "활동종료"
          else:
               return "D" + str((today - recruit_enddate).days)
     
     @property
     def activity_name(self):
          return str(self.activity)
     
     @property
     def interest_name(self):
          return str(self.interest)
     
     @property
     def position_names(self):
          return ', '.join([str(position) for position in self.positions.all()])
     
     @property
     def city_names(self):
          return ', '.join([str(city) for city in self.cities.all()])
          

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
     noti_unread_cnt = models.IntegerField(default=0)
     
     @property
     def avatar(self):
          return self.user.avatar.url

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
               
               # create team notification
               TeamNotification.objects.create(
                    type="team_application",
                    to_team = self.team,
                    related = self
               )
               
               # send fcm notification to team
               

class TeamLike(models.Model):
     team = models.ForeignKey(Team, related_name="liked_by", on_delete=models.CASCADE)
     user = models.ForeignKey(User, related_name="team_likes", on_delete=models.CASCADE)