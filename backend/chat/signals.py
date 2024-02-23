from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import *
from .serializers import TeamMessageCreateSerialzier, TeamMessageSerializer


# def alert_private_chat_participant_exit(participant):
@receiver(post_save, sender=TeamChatParticipant)
def handle_team_chat_participant_pre_delete(sender, instance, created, **kwargs):
     if created:
          with transaction.atomic():
               # 팀장이 아닌 새로운 멤버가 채팅방에 들어올 경우
               chatroom = instance.chatroom
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

