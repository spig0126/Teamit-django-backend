from django.db import models

from user.models import User
from team.models import Team, TeamMembers

# private chats
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
     chatroom = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
     chatroom_name = models.CharField(max_length=50)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     # unread_cnt = models.PositiveIntegerField(default=0)

class PrivateMessage(models.Model):
     chatroom = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
     sender = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     content = models.CharField(max_length=255)
     timestamp = models.DateField(auto_now_add=True)
     
     class Meta:
          ordering = ['-timestamp']
     
     
# inquiry chats
class InquiryMessagaeType(models.TextChoices):
     TEAM = "T", "team"
     INQUIRER = "I", "inquirer"
     
class InquiryChatRoom(models.Model):
     id = models.AutoField(primary_key=True)
     last_msg = models.CharField(max_length=255, default='')
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     inquirer = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='inquiry_chat_rooms')
     team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='inquiry_chat_rooms')
     
     class Meta:
          ordering = ['-updated_at']
     
class InquiryMessage(models.Model):
     chatroom = models.ForeignKey(InquiryChatRoom, on_delete=models.CASCADE)
     type = models.CharField(max_length=1, choices=InquiryMessagaeType.choices)
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

# class TeamMessage(models.Model):
#      chatroom = models.ForeignKey(TeamChat, blank=True, null=True, on_delete=models.CASCADE)
#      sender = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
#      content = models.CharField(max_length=255)
#      timestamp = models.DateField(auto_now_add=True)
     
#      class Meta:
#           ordering = ['-timestamp']
     