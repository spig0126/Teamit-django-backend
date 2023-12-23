from django.db import models
from dateutil.relativedelta import *
from datetime import *
from django.conf import settings

from region.models import Province, City
from position.models import Position
from interest.models import Interest
from activity.models import Activity

# Choices
class Visibility(models.TextChoices):
     PUBLIC = "PU", "전체 공개"  # db에 저장되는 값: "PU", client에게 전달되는 정보: "전체 공개"
     PRIVATE = "PI", "비공개"
     FOLLOWERS = "FO", "팔로우 공개"

class Sex(models.TextChoices):
     FEMALE = "F", "여자"    
     MALE = "M", "남자"
     UNSPECIFIED = "U", "선택하지 않을래요"

# Models
class User(models.Model):
     id = models.AutoField(primary_key=True)
     name = models.CharField(max_length=20, unique=True)
     interests = models.ManyToManyField(
          Interest,
          related_name="users"
     )
     positions = models.ManyToManyField(
          Position,
          related_name="users",
     )
     avatar = models.ImageField(upload_to='avatars/', default='avatars/1.png') 
     background = models.ImageField(upload_to='backgrounds/', default='backgrounds/bg1.png') 
     friends = models.ManyToManyField(
          'self',
          symmetrical=True
     )
     blocked_users = models.ManyToManyField(
          'self', 
          symmetrical=False
     )
     blocked_teams = models.ManyToManyField(
          settings.TEAM_MODEL,
          related_name="blocked_by"
     )
     
     def __str__(self):
          return self.name
     
     @property
     def interest_names(self):
          return ', '.join([str(interest) for interest in self.interests.all()])
     @property
     def position_names(self):
          return ', '.join([str(position) for position in self.positions.all()])
     @property
     def city_names(self):
          try:
               return ', '.join([str(city) for city in self.profile.cities.all()])
          except:
               return ''
     @property
     def activity_names(self):
          try:
               return ', '.join([str(activity) for activity in self.profile.activities.all()])
          except:
               return ''
     @property
     def keywords(self):
          try:
               return self.profile.keywords
          except:
               return ''
     

class UserProfile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
     visibility = models.CharField(
          max_length=2, choices=Visibility.choices, default=Visibility.PRIVATE
     )

     # 필수정보 (아래 항목들 + User의 positions, avatar, interests)
     birthdate = models.CharField(max_length=10, default="1900-01-01")
     sex = models.CharField(max_length=1, choices=Sex.choices, default=Sex.UNSPECIFIED)
     cities = models.ManyToManyField(
          City,
          related_name="users"
     )
     activities = models.ManyToManyField(
          Activity,
          related_name="users"
     )
     short_pr = models.CharField(max_length=50, default='', blank=True)

     # 선택 정보
     education = models.CharField(default='', blank=True)
     keywords = models.CharField(default='', blank=True)
     tools = models.CharField(default='', blank=True)
     experiences = models.CharField(default='', blank=True)
     certificates = models.CharField(default='', blank=True)
     links = models.CharField(default='', blank=True)

     def __str__(self):
          return self.user.name

     @property
     def age(self):
          today = date.today()
          birthdate = date.fromisoformat(self.birthdate)
          age = relativedelta(today, birthdate)
          return age.years

     @property
     def region(self):
          p_name = Province.objects.get(id=self.province_id)
          c_name = City.objects.get(id=self.city_id)
          if c_name == "전체":
               return p_name + "권"
          return p_name + " " + c_name


class FriendRequest(models.Model):
     from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
     to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
     accepted = models.BooleanField(default=False)
     
     def save(self, *args, **kwargs):
          is_new = self.pk is None
          super().save(*args, **kwargs)
          
          if is_new:
               from notification.models import Notification
               
               Notification.objects.create(
                    type="friend_request",
                    to_user = self.to_user,
                    related_id = self.id,
               )
          
class UserLikes(models.Model):
     from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
     to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_by')