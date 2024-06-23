from django.db import models

from user.models import User, UserProfile
from team.models import Team


class UserSearchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_searches")
    search_query = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now=True)
    searched_user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            search_history = UserSearchHistory.objects.filter(user=self.user)
            search_history_cnt = search_history.count()

            if search_history_cnt > 30:
                histories_to_delete = search_history_cnt - 30
                oldest_history_pks = search_history.order_by("timestamp").values_list('pk', flat=True)[
                                     :histories_to_delete]
                UserSearchHistory.objects.filter(pk__in=oldest_history_pks).delete()


class TeamSearchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_searches")
    search_query = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now=True)
    searched_team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            search_history = TeamSearchHistory.objects.filter(user=self.user)
            search_history_cnt = search_history.count()

            if search_history_cnt > 30:
                histories_to_delete = search_history_cnt - 30
                oldest_history_pks = search_history.order_by("timestamp").values_list('pk', flat=True)[
                                     :histories_to_delete]
                TeamSearchHistory.objects.filter(pk__in=oldest_history_pks).delete()
