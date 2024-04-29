from django.db import models

from user.models import User, PriorityLevels

class ProfileCard(models.Model):
     user = models.OneToOneField(User, verbose_name='profile_card', related_name='profile_card', primary_key=True, on_delete=models.CASCADE)
     bg_idx = models.PositiveSmallIntegerField(default=0)
     badge_bg_idx = models.PositiveSmallIntegerField(default=0)
     badge_one = models.ImageField(default ='')
     badge_two = models.ImageField(default='')
     interest = models.PositiveSmallIntegerField(choices=PriorityLevels.choices, default=PriorityLevels.HIGH)
     position = models.PositiveSmallIntegerField(choices=PriorityLevels.choices, default=PriorityLevels.HIGH)