from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import TeamPermission, TeamMembers, Team
from chat.models import TeamChatRoom, TeamChatParticipant
from user.models import User
from chat.serializers import TeamMessageCreateSerialzier, TeamMessageSerializer

@receiver(pre_delete, sender=User)
def handle_user_pre_delete(sender, instance, **kwargs):
     change_team_creator_when_user(instance)
     update_team_permissions(instance)
     instance.delete()


def change_team_creator_when_user(user):
     '''
     탈퇴한 사용자가 팀장일 경우 -> 한 멤버 무작위로 찾아 팀장으로 설정. 다른 멤버 없음 팀 삭제
     '''
     with transaction.atomic():
          teams = Team.objects.filter(creator=user)
          for team in teams:
               other_member_user = team.members.exclude(user).first()
               if other_member_user is not None:
                    team.creator = other_member_user
                    team.save()


def update_team_permissions(user):
     '''
     탈퇴한 사용자가 responder일 경우 -> responder를 팀장으로 바꾸기
     '''
     with transaction.atomic():
          permissions = TeamPermission.objects.filter(responder=user)
          for permission in permissions:
               permission.responder = permission.team.creator
               permission.save()

################################################################

@receiver(post_save, sender=Team)
def create_team_all_chatroom(sender, instance, created, **kwargs):
     if created:
          with transaction.atomic():
               TeamChatRoom.objects.create(
                    team=instance, 
                    name='전체방', 
                    background='0xff00FFD1'
               )
               
@receiver(post_save, sender=TeamMembers)
def add_new_member_to_all_chatroom(sender, instance, created, **kwargs):
     if created:
          with transaction.atomic():
               chatroom = TeamChatRoom.objects.filter(team=instance.team).order_by('created_at').first()
               
               # 새로운 멤버가 채팅방에 들어올 경ㅇ
               if not chatroom.participants.filter(pk=instance.user.pk).exists():
                    print(TeamChatParticipant.objects.create(
                         chatroom=chatroom,
                         user=instance.user,
                         member=instance
                    ))
               
               # 팀장이 아닌 새로운 멤버가 채팅방에 들어올 경우
               if chatroom.participants.count() > 1:
                    channel_layer = get_channel_layer()
                    chatroom_name = f"team_chat_{chatroom.id}"
                    announcement = {
                         'chatroom': chatroom.id,
                         'content': f'{instance.user} / {instance.position} 님이 입장했습니다',
                         'is_msg': False
                    }
                    serializer = TeamMessageCreateSerialzier(data=announcement)
                    serializer.is_valid(raise_exception=True)
                    message_instance = serializer.save()
                    message = TeamMessageSerializer(message_instance, context={'unread_cnt': 0}).data
                    async_to_sync(channel_layer.group_send)(
                         chatroom_name,
                         {
                              "type": "msg",
                              "message": message
                         }
                    )