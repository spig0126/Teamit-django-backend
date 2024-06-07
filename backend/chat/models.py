from django.db import models
from django.core.files.storage import default_storage

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
     
     @property
     def participant_names(self):
          return ', '.join([str(user) for user in self.participants.all()])
     
     class Meta:
          ordering = ['-updated_at']
          
     
class PrivateChatParticipant(models.Model):
     chatroom = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
     custom_name = models.CharField(max_length=50, null=True, blank=True)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
     unread_cnt = models.PositiveIntegerField(default=0)
     alarm_on = models.BooleanField(default=True)
     is_online = models.BooleanField(default=False)
     last_read_time = models.DateTimeField(auto_now=True)
     
     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self._other_user = None
     
     def _get_other_user(self):
          if self._other_user is None:
               self._other_user = self.chatroom.participants.exclude(pk=self.user.pk).first()
          return self._other_user
     
     @property
     def user_pk(self):
          return self.user.pk
     
     @property
     def chatroom_pk(self):
          return self.chatroom.pk
     
     @property
     def other_user_pk(self):
          other_user = self._get_other_user()
          try:
               return other_user.pk
          except Exception:
               return None
     
     @property
     def other_user_name(self):
          other_user = self._get_other_user()
          try:
               return other_user.name
          except Exception:
               return '(알 수 없음)'
     
     @property
     def chatroom_name(self):
          return self.custom_name or self.other_user_name

     @property
     def avatar(self):
          other_user = self._get_other_user()
          try:
               return default_storage.url(other_user.avatar.url)
          except Exception:
               return default_storage.url('avatars/default.png')
     
     @property
     def background(self):
          other_user = self._get_other_user()
          try:
               return default_storage.url(other_user.background)
          except Exception:
               return ''
     
     @property
     def updated_at(self):
          return self.chatroom.updated_at.isoformat()
     
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
               return default_storage.url('avatars/default.png')
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
     # inquirer_last_read_time = models.DateTimeField(auto_now_add=True)
     # responder_last_read_time = models.DateTimeField(auto_now_add=True)
     
     @property
     def inquirer_chatroom_name(self):
          return self.team.name
     
     @property
     def responder_chatroom_name(self):
          return self.team.name + ' > ' + self.inquirer.name
     
     @property
     def inquirer_avatar(self):
          return self.inquirer.avatar.url
     
     @property
     def team_image(self):
          return self.team.image.url
     
     @property
     def team_background(self):
          return ''
     
     @property
     def inquirer_background(self):
          return self.inquirer.background.url

     @property
     def responder(self):
          return self.team.responder or None
     
     @property
     def inquirer_name(self):
          return self.inquirer.name
     
     @property
     def responder_pk(self):
          return self.team.responder.pk
     
     @property
     def inquirer_pk(self):
          return self.inquirer.pk
     
     @property
     def team_name(self):
          return self.team.name
     
     
     class Meta:
          ordering = ['-updated_at']

class InquiryMessage(models.Model):
     chatroom = models.ForeignKey(InquiryChatRoom, on_delete=models.CASCADE, related_name="messages")
     sender = models.CharField(max_length=1, choices=InquiryRoleType.choices, blank=True, null=True)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
     team = models.ForeignKey(Team, blank=True, null=True, on_delete=models.SET_NULL)
     content = models.CharField(max_length=255)
     timestamp = models.DateTimeField(auto_now_add=True)
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
                    return default_storage.url('teams/default.png')
               return self.team.image.url
          else:
               if self.user is None:
                    return default_storage.url('avatars/default.png')
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
     last_msg = models.CharField(max_length=255, default='')
     participants = models.ManyToManyField(
          User, 
          through="TeamChatParticipant"
     )
     
     @property
     def participant_names(self):
          return ', '.join([f'{str(p.user)}, {p.name}' for p in TeamChatParticipant.objects.filter(chatroom=self)])
     
     class Meta:
          ordering = ['-updated_at']

class TeamChatParticipant(models.Model):
     id = models.AutoField(primary_key=True)
     chatroom = models.ForeignKey(TeamChatRoom, blank=True, null=True, on_delete=models.CASCADE)
     user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
     member = models.ForeignKey(TeamMembers, related_name="participants", blank=True, null=True, on_delete=models.SET_NULL)
     is_online = models.BooleanField(default=False)
     last_read_time = models.DateTimeField(auto_now=True)
     unread_cnt = models.PositiveIntegerField(default=0)
     alarm_on = models.BooleanField(default=True)
     entered_chatroom_at = models.DateTimeField(auto_now_add=True)
     
     @property
     def chatroom_pk(self):
          return self.chatroom.pk
     
     @property
     def chatroom_name(self):
          return self.chatroom.name
     
     @property
     def chatroom_avatar(self):
          return ''
     
     @property
     def chatroom_last_msg(self):
          return self.chatroom.last_msg
     
     @property
     def chatroom_updated_at(self):
          return self.chatroom.updated_at.isoformat()
     
     @property
     def chatroom_background(self):
          return self.chatroom.background
     
     @property
     def other_participant_names(self):
          return self.chatroom.participant_names
     
     @property
     def user_pk(self):
          return self.user.pk
     
     @property
     def team_name(self):
          return self.chatroom.team.name
     
     @property
     def name(self):
          if self.user is None:
               return '(알 수 없음)'
          if self.member is None:
               return self.user.name
          return self.member.name
     
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
          try:
               return self.member.name
          except Exception:
               return '(알 수 없음)'
     
     @property
     def avatar(self):
          if not self.is_msg:
               return ''
          try:
               return self.user.avatar.url
          except Exception:
               return default_storage.url('avatars/default.png')
     
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
     