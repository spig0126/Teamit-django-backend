from django.db.models.signals import pre_delete, post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import *
from .serializers import TeamMessageCreateSerialzier, TeamMessageSerializer, PrivateMessageCreateSerializer, \
    InquiryMessageCreateSerializer, PrivateMessageSerializer, InquiryMessageSerializer


@receiver(post_save, sender=InquiryChatRoom)
def create_inquiry_chat_participants(sender, instance, created, **kwargs):
    if not created:
        return
    with transaction.atomic():
        InquiryChatParticipant.objects.create(chatroom=instance, is_inquirer=True)
        InquiryChatParticipant.objects.create(chatroom=instance, is_inquirer=False)


@receiver(pre_delete, sender=User)
def delete_chat_participant_when_user_delete(sender, instance, **kwargs):
    InquiryChatParticipant.objects.filter(is_inquirer=True, chatroom__inquirer=instance).delete()


@receiver(pre_delete, sender=Team)
def delete_chat_participant_when_team_delete(sender, instance, **kwargs):
    InquiryChatParticipant.objects.filter(is_inquirer=False, chatroom__team=instance).delete()


'''
CHATROOM CREATE
'''


@receiver(post_save, sender=PrivateChatParticipant)
def alert_status_consumer_of_new_private_chatroom(sender, instance, created, **kwargs):
    if not created:
        return
    chatroom = instance.chatroom
    status_message = create_status_message({
        'id': chatroom.pk,
        'name': instance.chatroom_name,
        'avatar': instance.avatar,
        'background': instance.background,
        'updated_at': chatroom.updated_at.astimezone(
            timezone.get_current_timezone()).isoformat()
    })

    chatroom_name = f'status_{instance.user.pk}'
    async_to_sync(get_channel_layer().group_send)(
        chatroom_name,
        {
            "type": "msg",
            "chat_type": "private",
            'message': status_message
        }
    )


@receiver(post_save, sender=TeamChatParticipant)
def alert_status_consumer_of_new_team_chatroom(sender, instance, created, **kwargs):
    if not created:
        return
    chatroom = instance.chatroom
    status_message = create_status_message({
        'id': chatroom.pk,
        'name': chatroom.name,
        'avatar': '',
        'background': chatroom.background,
        'updated_at': chatroom.updated_at.astimezone(
            timezone.get_current_timezone()).isoformat()
    })

    chatroom_name = f'status_{instance.user.pk}'
    async_to_sync(get_channel_layer().group_send)(
        chatroom_name,
        {
            "type": "msg",
            "chat_type": "inquiry",
            'message': status_message
        }
    )


@receiver(post_save, sender=InquiryChatParticipant)
def alert_status_consumer_of_new_inquiry_chatroom(sender, instance, created, **kwargs):
    if not created:
        return
    chatroom = instance.chatroom
    status_message = create_status_message({
        'id': chatroom.pk,
        'name': chatroom.name,
        'avatar': '',
        'background': chatroom.background,
        'updated_at': chatroom.updated_at.astimezone(
            timezone.get_current_timezone()).isoformat()
    })

    user_pk = chatroom.inquirer_pk if instance.is_inquirer else chatroom.responder_pk
    chatroom_name = f'status_{user_pk}'
    async_to_sync(get_channel_layer().group_send)(
        chatroom_name,
        {
            "type": "msg",
            "chat_type": "inquiry",
            "team_id": chatroom.team.pk,
            'message': status_message
        }
    )


'''
CHAT PARTICIPANT CREATE 
'''


@receiver(post_save, sender=PrivateChatParticipant)
def send_enter_announcement_when_private_chat_participant_created(sender, instance, created, **kwargs):
    if created:
        send_chatroom_announcement(instance.chatroom, instance.name, '', 'private', 'enter')


@receiver(post_save, sender=InquiryChatParticipant)
def send_enter_announcement_when_inquiry_chat_participant_created(sender, instance, created, **kwargs):
    if created:
        send_chatroom_announcement(instance.chatroom, instance.name, '', 'inquiry', 'enter')


@receiver(post_save, sender=TeamChatParticipant)
def send_enter_announcement_when_team_chat_participant_created(sender, instance, created, **kwargs):
    if created:
        send_chatroom_announcement(instance.chatroom, instance.name, instance.position, 'team', 'enter')


'''
CHAT PARTICIPANT DELETE
'''


@receiver(pre_delete, sender=PrivateChatParticipant)
def handle_private_chat_participant_delete(sender, instance, **kwargs):
    try:
        if PrivateChatParticipant.objects.filter(chatroom=instance.chatroom).count() == 1:
            pre_delete.disconnect(handle_private_chat_participant_delete, sender=PrivateChatParticipant)
            instance.chatroom.delete()
            return
        send_offline_msg(instance.chatroom, instance.user.pk, 'private')
        send_chatroom_announcement(instance.chatroom, instance.name, '', 'private', 'exit')
    except AttributeError:
        return


@receiver(pre_delete, sender=TeamChatParticipant)
def handle_team_chat_participant_delete(sender, instance, **kwargs):
    try:
        if TeamChatParticipant.objects.filter(chatroom=instance.chatroom).count() == 1:
            pre_delete.disconnect(handle_team_chat_participant_delete, sender=TeamChatParticipant)
            instance.chatroom.delete()
            return
        send_offline_msg(instance.chatroom, instance.user.pk, 'team')
        send_chatroom_announcement(instance.chatroom, instance.name, instance.position, 'team', 'exit')
    except AttributeError:
        return


@receiver(pre_delete, sender=InquiryChatParticipant)
def handle_inquiry_chat_participant_delete(sender, instance, **kwargs):
    try:
        if InquiryChatParticipant.objects.filter(chatroom=instance.chatroom).count() == 1:
            pre_delete.disconnect(handle_inquiry_chat_participant_delete, sender=InquiryChatParticipant)
            instance.chatroom.delete()
            return
        user_pk = instance.chatroom.inquirer.pk if instance.is_inquirer else instance.chatroom.team.responder.pk
        send_offline_msg(instance.chatroom, user_pk, 'inquiry')
        send_chatroom_announcement(instance.chatroom, instance.name, '', 'inquiry', 'exit')
    except AttributeError:
        return


def send_offline_msg(chatroom, user_pk, chat_type):
    channel_layer = get_channel_layer()
    chatroom_name = f'{chat_type}_chat_{chatroom.pk}'
    async_to_sync(channel_layer.group_send)(
        chatroom_name,
        {
            "type": "offline",
            "message": {
                "user": user_pk
            }
        }
    )


def send_chatroom_announcement(chatroom, name, position, chat_type, action):
    channel_layer = get_channel_layer()
    action_content = '퇴장했습니다' if action == 'exit' else '입장했습니다'
    data = {
        'chatroom': chatroom.pk,
        'content': f'{name} / {position} 님이 {action_content}' if position else f'{name} 님이 {action_content}',
        'is_msg': False
    }
    message = create_announce_msg(chat_type, data)
    chatroom_name = f'{chat_type}_chat_{chatroom.pk}'
    async_to_sync(channel_layer.group_send)(
        chatroom_name,
        {
            "type": 'msg',
            "message": message
        }
    )


def create_announce_msg(chat_type, data):
    create_serializer = {
        'private': PrivateMessageCreateSerializer,
        'team': TeamMessageCreateSerialzier,
        'inquiry': InquiryMessageCreateSerializer
    }
    detail_serializer = {
        'private': PrivateMessageSerializer,
        'team': TeamMessageSerializer,
        'inquiry': InquiryMessageSerializer
    }

    try:
        serializer = create_serializer[chat_type](data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return detail_serializer[chat_type](instance, context={'unread_cnt': 0}).data
    except ValidationError as e:
        print('error', e.detail)


def create_status_message(updates):
    base = {
        'id': '',
        'name': '',
        'avatar': '',
        'background': '',
        'last_msg': '',
        'updated_at': '',
        'update_unread_cnt': False
    }
    status_message = {key: updates.get(key, base.get(key)) for key in base}
    return status_message
