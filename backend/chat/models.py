from django.db import models

from user.models import User
from team.models import Team, TeamMembers

# private chats
class PrivateChatRoom(models.Model):
     id = models.AutoField(primary_key=True)
     last_msg = models.CharField(max_length=255, default='')
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     last_msg = models.CharField(max_length=255)
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
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
     unread_cnt = models.PositiveIntegerField(default=0)
     alarm_on = models.BooleanField(default=True)
     is_online = models.BooleanField(default=False)
     last_read_time = models.DateTimeField(auto_now=True)
     
     @property
     def avatar(self):
          other_user = self.chatroom.participants.exclude(user=self.user).first()
          if other_user is None:
               return 'avatars/default.png'
          return other_user.avatar.url
     
     @property
     def background(self):
          other_user = self.chatroom.participants.exclude(user=self.user).first()
          if other_user is None:
               return ''
          return other_user.background.url
     
     @property
     def updated_at(self):
          return self.chatroom.updated_at
     
     @property
     def last_msg(self):
          return self.chatroom.last_msg

class PrivateMessage(models.Model):
     chatroom = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE, related_name='messages')
     sender = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     content = models.CharField(max_length=255)
     timestamp = models.DateTimeField(auto_now_add=True)
     is_msg = models.BooleanField(default=True)
     
     @property
     def name(self):
          if not self.is_msg:
               return ''
          elif self.sender is None:
               return '(알 수 없음)'
          else:
               return self.sender.name
     
     @property
     def avatar(self):
          if not self.is_msg:
               return ''
          elif self.sender is None:
               return 'avatars/default.png'
          else:
               return self.sender.avatar.url
     
     @property
     def background(self):
          if not self.is_msg:
               return ''
          elif self.sender is None:
               return ''
          else:
               return self.sender.background.url

     class Meta:
          ordering = ['-timestamp']
     
     
# inquiry chats
class InquiryRoleType(models.TextChoices):
     TEAM = "T", "team"
     INQUIRER = "I", "inquirer"
     
class InquiryChatRoom(models.Model):
     id = models.AutoField(primary_key=True)
     last_msg = models.CharField(max_length=255, default='')
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     inquirer = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='inquiry_chat_rooms')
     team = models.ForeignKey(Team, blank=True, null=True, on_delete=models.SET_NULL, related_name='inquiry_chat_rooms')
     inquirer_unread_cnt = models.PositiveIntegerField(default=0)
     responder_unread_cnt = models.PositiveIntegerField(default=0)
     inquirer_alarm_on = models.BooleanField(default=True)
     responder_alarm_on = models.BooleanField(default=True)
     inquirer_is_online = models.BooleanField(default=False)
     responder_is_online = models.BooleanField(default=False)
     inquirer_last_read_time = models.DateTimeField(auto_now_add=True)
     responder_last_read_time = models.DateTimeField(auto_now_add=True)
     
     @property
     def responder(self):
          if self.team is None:
               return None
          return self.team.responder
     class Meta:
          ordering = ['-updated_at']

class InquiryMessage(models.Model):
     chatroom = models.ForeignKey(InquiryChatRoom, on_delete=models.CASCADE, related_name="messages")
     sender = models.CharField(max_length=1, choices=InquiryRoleType.choices, blank=True, null=True)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     team = models.ForeignKey(Team, blank=True, null=True, on_delete=models.SET_NULL)
     content = models.CharField(max_length=255)
     timestamp = models.DateField(auto_now_add=True)
     is_msg = models.BooleanField(default=True)
     
     @property
     def name(self):
          if self.sender == InquiryRoleType.TEAM:
               if self.team is None:
                    return '(알 수 없음)'
               return self.team.name
          else:
               if self.user is None:
                    return '(알 수 없음)'
               return self.user.name
          
     @property
     def avatar(self):
          if self.sender == InquiryRoleType.TEAM:
               if self.team is None:
                    return 'teams/default.png'
               return self.team.image.url
          else:
               if self.user is None:
                    return 'avatars/default.png'
               return self.user.avatar.url
     
     @property
     def background(self):
          if self.sender == InquiryRoleType.TEAM:
               return ''
          else:
               if self.user is None:
                    return ''
               return self.user.background.url
          
     class Meta:
          ordering = ['-timestamp']

# team chats
class TeamChatRoom(models.Model):
     id = models.AutoField(primary_key=True)
     team = models.ForeignKey(Team, on_delete=models.CASCADE)
     name = models.CharField(max_length=50)
     background = models.CharField(default='0xff00FFD1', max_length=10)
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     last_msg = models.CharField(max_length=255)
     participants = models.ManyToManyField(
          User, 
          through="TeamChatParticipant"
     )

class TeamChatParticipant(models.Model):
     id = models.AutoField(primary_key=True)
     chatroom = models.ForeignKey(TeamChatRoom, blank=True, null=True, on_delete=models.CASCADE)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
     member = models.ForeignKey(TeamMembers, related_name="participants", blank=True, null=True, on_delete=models.SET_NULL)
     is_online = models.BooleanField(default=False)
     last_read_time = models.DateTimeField(auto_now=True)
     unread_cnt = models.PositiveIntegerField(default=0)
     alarm_on = models.BooleanField(default=True)
     
     @property
     def name(self):
          if self.user is None:
               return '(알 수 없음)'
          return self.user.name
     
     @property 
     def position(self):
          if self.user is None or self.member is None:
               return ''
          else:
               return self.member.position.name
     class Meta:
          constraints = [
               models.UniqueConstraint(fields=['chatroom', 'user'], name='unique_team_chat_participant')
          ]

class TeamMessage(models.Model):
     chatroom = models.ForeignKey(TeamChatRoom, blank=True, null=True, on_delete=models.CASCADE, related_name="messages")
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     member = models.ForeignKey(TeamMembers, blank=True, null=True, on_delete=models.SET_NULL)
     content = models.CharField(max_length=255)
     timestamp = models.DateTimeField(auto_now_add=True)
     is_msg = models.BooleanField(default=True)
     
     @property
     def name(self):
          if not self.is_msg:
               return ''
          elif self.user is None:
               return '(알 수 없음)'
          return self.user.name
     
     @property
     def avatar(self):
          if not self.is_msg:
               return ''
          elif self.user is None:
               return 'avatars/default.png'
          return self.user.avatar.url
     
     @property
     def background(self):
          if not self.is_msg:
               return ''
          elif self.user is None:
               return ''
          elif self.member is None:
               return '0xff45474D'
          else:
               return self.member.background
     
     @property 
     def position(self):
          if not self.is_msg:
               return ''
          elif self.member is None or self.user is None:
               return ''
          else:
               return self.member.position.name

     class Meta:
          ordering = ['-timestamp']
     