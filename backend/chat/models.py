from django.db import models

from user.models import User
from team.models import Team, TeamMembers

# Create your models here.
class PrivateChatRoom(models.Model):
     id = models.AutoField(primary_key=True)
     last_msg = models.CharField(max_length=255, default='')
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     participants = models.ManyToManyField(
          User, 
          through="PrivateChatParticipant",
          related_name="private_chat_rooms"
     )
     
     class Meta:
          ordering = ['-updated_at']
     
class PrivateChatParticipant(models.Model):
     chatroom = models.ForeignKey(PrivateChatRoom, blank=True, null=True, on_delete=models.CASCADE)
     chatroom_name = models.CharField(max_length=50)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     # unread_cnt = models.PositiveIntegerField(default=0)

class PrivateMessage(models.Model):
     chatroom = models.ForeignKey(PrivateChatRoom, blank=True, null=True, on_delete=models.CASCADE)
     sender = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     content = models.CharField(max_length=255)
     timestamp = models.DateField(auto_now_add=True)
     
     class Meta:
          ordering = ['-timestamp']
     
# class TeamChat(models.Model):
#      id = models.AutoField(primary_key=True)
#      team = models.ForeignKey(Team, on_delete=models.CASCADE)
#      name = models.CharField(max_length=50)
#      last_msg = models.CharField(max_length=255)
#      created_at = models.DateTimeField(auto_now_add=True)
#      updated_at = models.DateTimeField(auto_now=True)
#      participants = models.ManyToManyField(
#           TeamMembers, 
#           through="TeamChatParticipant"
#      )

# class TeamChatParticipant(models.Model):
#      id = models.AutoField(primary_key=True)
#      team_chat = models.ForeignKey(TeamChat, blank=True, null=True, on_delete=models.CASCADE)
#      user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
#      member = models.ForeignKey(TeamMembers, blank=True, null=True, on_delete=models.SET_NULL)
