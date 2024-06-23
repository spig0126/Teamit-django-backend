import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F

from .models import *
from .serializers import *
from user.serializers import UserMinimalWithAvatarBackgroundDetailSerializer
from fcm_notification.tasks import send_fcm_to_user_task


class PrivateChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.participants_set = None
        self.alarm_on_particiapnts = None
        self.this_participant = None
        self.last_read_time = None
        self.participants = None
        self.other_participant = None
        self.online_participants = []
        self.loaded_cnt = 0
        self.chatroom = None

    async def connect(self):
        self.user = self.scope.get('user')
        self.chatroom_id = int(self.scope["url_route"]["kwargs"]["chatroom_id"])
        self.chatroom_name = f"private_chat_{self.chatroom_id}"
        is_valid = await self.get_chatroom_and_participants_info()
        if not is_valid:
            await self.close()
            return

        was_offline = await self.this_participant_was_offline()
        if was_offline:
            await self.mark_as_online()

        await self.join_chatroom()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
        await self.mark_as_offline()

    # Receive message from WebSocket (frontend -> channel)
    async def receive(self, text_data):
        data = json.loads(text_data)
        type = data["type"]
        message = data.get('message', None)

        if type == 'msg':
            await self.handle_message(message)
        elif type == 'history':
            await self.send_last_30_messages()
        elif type == 'exit':
            await self.handle_exit()
        elif type == 'update_alarm_status':
            await self.update_alarm_status()
        elif type == 'settings':
            await self.handle_settings()
        elif type == 'update_chatroom_name':
            await self.handle_update_chatroom_name(message)

    # ---------------------handle related---------------
    async def handle_message(self, message):
        msg_details = {
            'chatroom': self.chatroom_id,
            'sender': self.user.pk,
            'content': message['content']
        }
        message = await self.create_message(msg_details)
        await self.update_chatroom_last_msg(message['content'])
        await self.send_group_message('msg', message)
        await self.send_user_status_message(message)
        await self.update_offline_participant_unread_cnt()
        await self.send_offline_participants_fcm(message)

    async def handle_exit(self):
        await self.remove_this_participant_from_chatroom()
        await self.send_message('exit_successful', True)
        await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
        await self.close()

    async def handle_settings(self):
        participant_list = await self.get_participant_list()
        if participant_list[0]['id'] != self.user.pk:
            participant_list.reverse()
        alarm_on = self.this_participant.alarm_on
        type = 'settings'
        message = {
            'participant_list': participant_list,
            'alarm_on': alarm_on
        }
        await self.send_message(type, message)

    async def handle_update_chatroom_name(self, new_chatroom_name):
        await self.update_chatroom_name(new_chatroom_name)
        status_message = await self.create_status_message({
            'name': new_chatroom_name,
            'update_unread_cnt': False
        })
        message_info = {
            'type': 'msg',
            'chat_type': 'private',
            'message': status_message
        }

        for user in self.participants:
            await self.channel_layer.group_send(
                f'status_{user}',
                message_info
            )

    # ----------------EVENT RELATED------------------------------------

    async def online(self, event):
        user = event['message'].get('user', None)
        self.online_participants.append(user)
        await self.send_message(event['type'], event['message'])

    async def offline(self, event):
        user = event['message'].get('user', None)
        try:
            self.online_participants.remove(user)
        except Exception:
            pass
        # print('exit', self.user, user)
        # print(self.online_participants)

    async def msg(self, event):
        await self.send_message(event['type'], event['message'])

    async def exit(self, event):
        await self.send_message('msg', event['message'])
        await self.update_participant_info()

    async def alarm_change(self, event):
        return

    # ----------------UTILITY FUNCTIONS---------------------------------
    async def send_offline_participants_fcm(self, message):
        should_send, chatroom_name, user_pk = await self.alarm_on_offline_participants()
        if should_send:
            title = chatroom_name
            body = message['content']
            data = {
                'page': 'chat',
                'chatroom_name': title,
                'chatroom_id': str(self.chatroom_id),
                'chat_type': 'private'
            }
            send_fcm_to_user_task.delay(user_pk, title, body, data)


    async def send_message(self, type, message):
        await self.send(text_data=json.dumps({
            'type': type,
            'message': message
        }))

    async def send_is_alone_message(self):
        await self.send_message('is_alone', len(self.participants) == 1)

    async def send_last_30_messages(self):
        message = await self.get_last_30_messages()
        await self.send_message('history', message)

    async def send_group_message(self, type, message):
        await self.channel_layer.group_send(
            self.chatroom_name, {"type": type, "message": message}
        )

    async def join_chatroom(self):
        await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
        await self.accept()
        await self.send_is_alone_message()
        await self.send_last_30_messages()

    async def mark_as_online(self):
        '''
          Alerts the frontend of 'online' status and updates participant info.
          '''
        data = {
            'user': self.user.pk,
            'last_read_time': self.last_read_time.isoformat()
        }

        await self.update_this_participant_online()
        await self.send_group_message('online', data)

    async def mark_as_offline(self):
        '''
          Alerts others of the disconnect and updates participant info as offline.
          '''
        if self.chatroom is not None:
            await self.send_group_message('offline', {'user': self.user.pk})
            await self.update_this_participant_offline()

    async def send_user_status_message(self, message):
        status_message = await self.create_status_message({
            'last_msg': message.get('content'),
            'updated_at': message.get('timestamp'),
        })
        message_info = {
            'type': 'msg',
            'chat_type': 'private',
            'message': status_message
        }

        for user in self.participants:
            # print(self.online_participants)
            status_message['update_unread_cnt'] = (user not in self.online_participants)
            await self.channel_layer.group_send(
                f'status_{user}',
                message_info
            )

    async def create_status_message(self, updates):
        base = {
            'id': self.chatroom_id,
            'name': '',
            'avatar': '',
            'background': '',
            'last_msg': '',
            'updated_at': '',
            'update_unread_cnt': None
        }
        status_mesage = {key: updates.get(key, base.get(key)) for key in base}
        return status_mesage

    # ----------------DATABASE RELATED------------------------------------
    @database_sync_to_async
    def alarm_on_offline_participants(self):
        other_participant = PrivateChatParticipant.objects.filter(chatroom=self.chatroom, is_online=False, alarm_on=True).exclude(
            user=self.user).first()
        if other_participant:
            return True, other_participant.chatroom_name, other_participant.user.pk
        return False, None, None

    @database_sync_to_async
    def update_chatroom_name(self, chatroom_name):
        self.this_participant.custom_name = chatroom_name
        self.this_participant.save()

    @database_sync_to_async
    def get_participant_list(self):
        participants = self.chatroom.participants.all()
        return UserMinimalWithAvatarBackgroundDetailSerializer(participants, many=True).data

    @database_sync_to_async
    def update_alarm_status(self):
        self.this_participant.alarm_on = not self.this_participant.alarm_on
        self.this_participant.save()

    @database_sync_to_async
    def delete_chatroom(self):
        PrivateChatRoom.objects.get(pk=self.chatroom_id).delete()

    @database_sync_to_async
    def update_participant_info(self):
        participants = PrivateChatParticipant.objects.filter(chatroom=self.chatroom)
        self.participants = list(participants.values_list('user', flat=True))
        self.other_participant = None
        self.online_participants = list(participants.filter(is_online=True).values_list('user', flat=True))

    @database_sync_to_async
    def remove_this_participant_from_chatroom(self):
        self.chatroom = None
        self.participants = None
        self.this_participant = None
        self.other_participant = None
        self.online_participants = None
        PrivateChatParticipant.objects.get(chatroom=self.chatroom_id, user=self.user.pk).delete()

    @database_sync_to_async
    def update_offline_participant_unread_cnt(self):
        PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id, is_online=False).exclude(
            user=self.user).update(unread_cnt=F('unread_cnt') + 1)

    @database_sync_to_async
    @transaction.atomic
    def update_chatroom_last_msg(self, content):
        self.chatroom.last_msg = content
        self.chatroom.save()

    @database_sync_to_async
    @transaction.atomic
    def create_message(self, data):
        try:
            serializer = PrivateMessageCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return PrivateMessageSerializer(instance).data
        except ValidationError as e:
            self.send_message('error', e.detail)

    @database_sync_to_async
    @transaction.atomic
    def update_this_participant_online(self):
        self.this_participant.unread_cnt = 0
        self.this_participant.is_online = True
        self.this_participant.save()
        self.last_read_time = self.this_participant.last_read_time.astimezone(timezone.get_current_timezone())
        self.online_participants.append(self.user.pk)

    @database_sync_to_async
    def update_this_participant_offline(self):
        try:
            self.online_participants.remove(self.user.pk)
        except ValueError:
            pass
        try:
            if self.user not in self.online_participants:
                self.this_participant.is_online = False
                self.this_participant.unread_cnt = 0
                self.this_participant.save()
        except:
            pass

    @database_sync_to_async
    def update_other_participant(self):
        self.other_participant = PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id).exclude(
            user=self.user).first()
        return self.other_participant

    @database_sync_to_async
    def this_participant_was_offline(self):
        return not self.this_participant.is_online

    @database_sync_to_async
    def other_participant_is_offline(self):
        return self.other_participant.pk not in set(self.online_participants)

    @database_sync_to_async
    def get_other_participant_info(self):
        return self.other_participant.chatroom_name, self.other_participant.user.pk

    @database_sync_to_async
    def get_chatroom_and_participants_info(self):
        try:
            self.chatroom = PrivateChatRoom.objects.get(id=self.chatroom_id)
            participants = PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id)
            self.participants = list(participants.values_list('user', flat=True))
            self.participants_set = {self.chatroom.user1.pk, self.chatroom.user2.pk}
            self.this_participant = participants.get(user=self.user)
            self.this_participant.is_online = True
            self.this_participant.save()
            self.other_participant = participants.exclude(user=self.user).first()
            self.last_read_time = self.this_participant.last_read_time.astimezone(timezone.get_current_timezone())
            self.online_participants = list(participants.filter(is_online=True).values_list('user', flat=True))
            self.alarm_on_particiapnts = set(participants.filter(alarm_on=True).values_list('user', flat=True))
            return True
        except:
            return False

    @database_sync_to_async
    def get_last_30_messages(self):
        last_read_time_list = PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id,
                                                                    is_online=False).values_list('last_read_time',
                                                                                                 flat=True)
        messages = self.chatroom.messages.filter(timestamp__gte=self.this_participant.entered_chatroom_at).all()[
                   self.loaded_cnt:self.loaded_cnt + 30]
        self.loaded_cnt += 30
        return PrivateMessageSerializer(messages, many=True, context={"last_read_time_list": last_read_time_list}).data
