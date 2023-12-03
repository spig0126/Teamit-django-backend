from django.db import models

from user.models import User
from team.models import Team, TeamApplication

class Notification(models.Model):
     type = models.CharField(max_length=30)
     to_user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE, default=55)
     related_id = models.PositiveIntegerField()
     created_at = models.DateTimeField(auto_now_add=True, blank=True)
     is_read = models.BooleanField(default=False)

class TeamNotification(models.Model):
     type = models.CharField(max_length=30)
     to_team = models.ForeignKey(Team, related_name="notifications", on_delete=models.CASCADE)
     related = models.ForeignKey(TeamApplication, related_name="notifications", on_delete=models.CASCADE)
     created_at = models.DateTimeField(auto_now_add=True)
     is_read = models.BooleanField(default=False)