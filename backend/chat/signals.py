from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import *
from .serializers import TeamMessageCreateSerialzier, TeamMessageSerializer


@receiver(post_save, sender=TeamChatParticipant)
def handle_team_chat_participant_save(sender, instance, created, **kwargs):
     if created:
          with transaction.atomic():
               # 팀장이 아닌 새로운 멤버가 채팅방에 들어올 경우
               chatroom = instance.chatroom
               if chatroom.participants.count() > 1:
                    send_chatroom_announcement(chatroom, instance, 'enter')


@receiver(pre_delete, sender=TeamChatParticipant)
def handle_team_chat_partcipant_delete(sender, instance, **kwargs):
     chatroom = instance.chatroom
     send_chatroom_announcement(chatroom, instance, 'exit')


def send_chatroom_announcement(chatroom, participant, action):
     channel_layer = get_channel_layer()
     chatroom_name = f'team_chat_{chatroom.id}'
     action_text = '입장했습니다' if action == 'enter' else '퇴장했습니다'
     announcement = {
          'chatroom': chatroom.id,
          'content': f'{participant.name} / {participant.position} 님이 {action_text}',
          'is_msg': False
     }
     serializer = TeamMessageCreateSerialzier(data=announcement)
     if serializer.is_valid(raise_exception=True):
          message_instance = serializer.save()
          message = TeamMessageSerializer(message_instance, context={'unread_cnt': 0}).data
          async_to_sync(channel_layer.group_send)(
               chatroom_name,
               {
                    "type": action,
                    "message": message
               }
          ) 