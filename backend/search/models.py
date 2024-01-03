from django.db import models

from user.models import User, UserProfile
from team.models import Team

# Create your models here.
class UserSearchHistory(models.Model):
     id = models.AutoField(primary_key=True)
     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_searches")
     search_query = models.CharField(max_length=50)
     timestamp = models.DateTimeField(auto_now=True)
     searched_user = models.ForeignKey(User, on_delete=models.CASCADE)
     
     def save(self, *args, **kwargs):
          super().save(*args, **kwargs)
          # Check if the user has more than 30 search histories
          search_history = UserSearchHistory.objects.filter(user=self.user)
          search_history_cnt = search_history.count()

          if search_history_cnt > 30:
               # Calculate how many hitories to delete
               histories_do_delete = search_history_cnt - 30

               # Get the oldest histories to delete
               oldest_history = search_history.order_by("timestamp")[:histories_do_delete]

               # Delete the oldest histories
               oldest_history.delete()
     
class TeamSearchHistory(models.Model):
     id = models.AutoField(primary_key=True)
     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_searches")
     search_query = models.CharField(max_length=50)
     timestamp = models.DateTimeField(auto_now=True)
     searched_team = models.ForeignKey(Team, on_delete=models.CASCADE)
     
     def save(self, *args, **kwargs):
          super().save(*args, **kwargs)
          # Check if the user has more than 30 search histories
          search_history = TeamSearchHistory.objects.filter(user=self.user)
          search_history_cnt = search_history.count()

          if search_history_cnt > 30:
               # Calculate how many hitories to delete
               histories_do_delete = search_history_cnt - 30

               # Get the oldest histories to delete
               oldest_history = search_history.order_by("timestamp")[:histories_do_delete]

               # Delete the oldest histories
               oldest_history.delete()