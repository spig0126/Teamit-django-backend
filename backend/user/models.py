from django.db import models
from dateutil.relativedelta import *
from datetime import date

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

# class Category(models.TextChoices):
#      ALL = "ALL", "전체"
#      PROJECT = "PRO", "프로젝트"
#      COMPETITION = "CMP", "서포터즈/공모전"
#      CLUB = "CLB", "동아리/학회"
#      STARTUP = "STU", "창업"
#      STUDY = "STY", "스터디"

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
     avatar = models.JSONField(default=dict)
     notifications = models.BooleanField(default=False)

class UserProfile(models.Model):
     user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
     visibility = models.CharField(
          max_length=2, choices=Visibility.choices, default=Visibility.PRIVATE
     )

     # 필수정보 (아래 항목들 + User의 positions, avatar, interests)
     birthdate = models.CharField(max_length=8, default="19000101")
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

     @property
     def user_name(self):
          return self.user.name

     @property
     def age(self):
          today = date.today()
          birthdate = date(self.birthdate)
          age = relativedelta(today, birthdate)
          return age.years

     @property
     def region(self):
          p_name = Province.objects.get(id=self.province_id)
          c_name = City.objects.get(id=self.city_id)
          if c_name == "전체":
               return p_name + "권"
          return p_name + " " + c_name