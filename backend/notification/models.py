from django.db import models
from django.db.models import F

from user.models import User
from team.models import Team, TeamApplication, TeamMembers

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
     
     def save(self, *args, **kwargs):
          is_new = self.pk is None
          super().save(*args, **kwargs)
          
          if is_new:
               # alert team members with new notification by updating noti_unread_cnt
               TeamMembers.objects.filter(team=self.to_team).update(noti_unread_cnt=F('noti_unread_cnt') + 1)