from django.db import models

class Notification(models.Model):
     type = models.CharField(max_length=20)
     related_id = models.PositiveIntegerField()
     created_at = models.DateTimeField(auto_now_add=True, blank=True)