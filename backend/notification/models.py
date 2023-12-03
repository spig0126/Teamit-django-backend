from django.db import models

from user.models import User

class Notification(models.Model):
     type = models.CharField(max_length=30)
     to_user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE, default=55)
     related_id = models.PositiveIntegerField()
     created_at = models.DateTimeField(auto_now_add=True, blank=True)
     is_read = models.BooleanField(default=False)