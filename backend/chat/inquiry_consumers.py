import json
from django.utils import timezone

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.exceptions import ValidationError
from django.db.models import F

from .models import *
from .serializers import *
from team.serializers import TeamBasicDetailForChatSerializer
from user.serializers import UserMinimalWithAvatarBackgroundDetailSerializer
from fcm_notification.tasks import send_fcm_to_user_task


class InquiryChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.before_last_read_time = None
        self.loaded_cnt = None
        self.chatroom_name = None
        self.chatroom_id = None
        self.user = None
        self.this_participant = None
        self.alarm_on_participants = None
        self.participants_set = None
        self.online_participants = None
        self.is_member = None
        self.is_inquirer = None
        self.is_responder = None
        self.responder = None
        self.inquirer = None
        self.team_name = None
        self.participants = None
        self.team_pk = None
        self.chatroom = None

    async def connect(self):
        self.user = self.scope.get('user')
        self.chatroom_id = int(self.scope["url_route"]["kwargs"]["chatroom_id"])
        self.chatroom_name = f"inquiry_chat_{self.chatroom_id}"
        self.is_responder = False
        self.loaded_cnt = 0

        is_valid = await self.get_chatroom_and_participants_info()
        if not is_valid:
            await self.close()
            return

        was_offline = await self.participant_was_offline()
        if was_offline:
            await self.update_participant_online()

        await self.update_online_participants()
        await self.join_chatroom()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
        if self.is_inquirer or self.is_responder:
            await self.mark_as_offline()

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
            await self.handle_update_alarm_status()
        elif type == 'settings':
            await self.handle_settings()

    # ---------------Handle related-------------------
    async def handle_message(self, message):
        msg_details = {
            'chatroom': self.chatroom_id,
            'sender': 'T' if self.is_responder else 'I',
            'content': message['content'],
        }
        message = await self.create_message(msg_details, 2 - len(set(self.online_participants)))
        await self.update_chatroom_last_msg(message['content'])
        await self.update_unread_cnt()
        await self.send_group_message('msg', message)
        await self.send_status_message(message)
        await self.send_offline_participants_fcm(message)

    async def handle_exit(self):
        await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
        await self.delete_this_participant()
        await self.send_message('exit_successful', True)
        await self.close()

    async def handle_settings(self):
        participants = await self.get_paricipants()
        participant_list = []

        if await self.is_inquirer_participant_exist(participants):
            data = UserMinimalWithAvatarBackgroundDetailSerializer(self.inquirer).data
            participant_list.append(data)
        if await self.is_responder_participant_exist(participants):
            data = TeamBasicDetailForChatSerializer(self.chatroom.team).data
            participant_list.append(data)

        if len(participant_list) == 2 and not self.is_inquirer:
            participant_list.reverse()

        alarm_on = self.this_participant.alarm_on
        type = 'settings'
        message = {
            'participant_list': participant_list,
            'alarm_on': alarm_on
        }
        await self.send_message(type, message)

    async def handle_update_alarm_status(self):
        new_alarm_status = await self.update_alarm_status()
        await self.send_group_message('alarm_change', {'user': self.user.pk, 'alarm_on': new_alarm_status})
        await self.send_status_alarm_message(new_alarm_status)

    # ---------------event related----------------------
    async def online(self, event):
        user = event['message'].get('user', None)
        self.online_participants.append(user)
        await self.send_message(event['type'], event['message'])

    async def offline(self, event):
        user = event['message'].get('user', None)
        try:
            self.online_participants.remove(user)
        except ValueError:
            pass
        await self.send_message(event['type'], event['message'])

    async def msg(self, event):
        await self.send_message(event['type'], event['message'])

    async def alarm_change(self, event):
        if event['message']['alarm_on']:
            self.alarm_on_participants.add(event['message']['user'])
        else:
            self.alarm_on_participants.discard(event['message']['user'])
        await self.send_message(event['type'], event['message'])

    # ----------------utility related-------------------
    async def send_status_alarm_message(self, new_alarm_status):
        status_message = {
            'id': self.chatroom_id,
            'name': '',
            'avatar': '',
            'background': '',
            'last_msg': '',
            'updated_at': '',
            'alarm_on': new_alarm_status
        }
        message_info = {
            'type': 'msg',
            'chat_type': 'inquiry',
            'message': status_message
        }
        channel_name = f'status_{self.user.pk}'
        await self.channel_layer.group_send(
            channel_name, message_info
        )

    async def send_status_message(self, message):
        # to user's chat status
        status_message = {
            'id': self.chatroom_id,
            'name': '',
            'avatar': '',
            'background': '',
            'last_msg': message.get('content'),
            'updated_at': message.get('timestamp'),
            'alarm_on': None
        }
        message_info = {
            'type': 'msg',
            'chat_type': 'inquiry',
            'filter': 'responder' if self.is_responder else 'inquirer',
            'message': status_message
        }

        for user_pk in self.participants_set:
            status_message['update_unread_cnt'] = user_pk not in set(self.online_participants)
            channel_name = f'status_{user_pk}'
            await self.channel_layer.group_send(
                channel_name, message_info
            )

        # to team inquiry status
        status_message = {
            'id': self.chatroom_id,
            'name': '',
            'avatar': '',
            'background': '',
            'last_msg': message.get('content'),
            'updated_at': message.get('timestamp')
        }
        message_info = {
            'type': 'msg',
            'message': status_message
        }
        channel_name = f'team_inquiry_status_{self.team_pk}'
        await self.channel_layer.group_send(
            channel_name, message_info
        )

    async def send_message(self, type, message):
        await self.send(text_data=json.dumps({
            'type': type,
            'message': message
        }))

    async def send_is_alone_message(self):
        is_alone = True
        if len(set(self.online_participants)) == 2:
            is_alone = False
        await self.send_message('is_alone', is_alone)

    async def send_recent_messages(self):
        message = await self.get_recent_messages()
        await self.send_message('history', message)

    async def send_last_30_messages(self):
        message = await self.get_last_30_messages()
        await self.send_message('history', message)

    async def join_chatroom(self):
        await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
        await self.accept()
        await self.send_is_alone_message()
        await self.send_user_roles()
        await self.send_recent_messages()

    async def mark_as_offline(self):
        if self.chatroom is not None:
            await self.send_group_message('offline', {'user': self.user.pk})
            await self.update_user_offline()

    async def send_group_message(self, type, message):
        await self.channel_layer.group_send(
            self.chatroom_name, {"type": type, "message": message}
        )

    async def send_user_roles(self):
        type = 'user_roles'
        message = {
            'is_inquirer': self.is_inquirer,
            'is_responder': self.is_responder,
            'is_member': self.is_member
        }
        await self.send_message(type, message)

    async def update_online_participants(self):
        if self.is_responder or self.is_inquirer:
            self.online_participants.append(self.user.pk)
            await self.send_group_message('online', {'user': self.user.pk,
                                                     'last_read_time': self.this_participant.last_read_time.astimezone(
                                                         timezone.get_current_timezone()).isoformat()})

    # ----------------DB related------------------------

    @database_sync_to_async
    def send_offline_participants_fcm(self, message):
        title = self.chatroom.team_chatroom_name if self.is_inquirer else self.chatroom.inquirer_chatroom_name
        body = message['content']
        data = {
            'page': 'chat',
            'chatroom_name': title,
            'chatroom_id': str(self.chatroom_id),
            'chat_type': 'inquiry'
        }
        alarm_on_offline_participants = (self.participants_set - set(self.online_participants)).intersection(
            self.alarm_on_participants)
        for participant in alarm_on_offline_participants:
            send_fcm_to_user_task.delay(participant, title, body, data)

    @database_sync_to_async
    def update_alarm_status(self):
        alarm_status = self.this_participant.alarm_on
        self.this_participant.alarm_on = not alarm_status
        self.this_participant.save()
        if alarm_status is True:
            self.alarm_on_participants.discard(self.user.pk)
        return not alarm_status

    @database_sync_to_async
    def delete_this_participant(self):
        self.this_participant.delete()

    @database_sync_to_async
    def update_unread_cnt(self):
        InquiryChatParticipant.objects.filter(chatroom=self.chatroom, is_inquirer=not self.is_inquirer).update(
            unread_cnt=F('unread_cnt') + 1)

    @database_sync_to_async
    @transaction.atomic
    def update_chatroom_last_msg(self, content):
        self.chatroom.last_msg = content
        self.chatroom.save()

    @database_sync_to_async
    @transaction.atomic
    def create_message(self, data, unread_cnt):
        try:
            serializer = InquiryMessageCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return InquiryMessageSerializer(instance, context={'unread_cnt': unread_cnt}).data
        except ValidationError as e:
            self.send_message('error', e.detail)

    @database_sync_to_async
    def get_recent_messages(self):
        if self.this_participant:
            before_last_read = InquiryMessageSerializer(
                self.chatroom.messages.filter(timestamp__gte=self.this_participant.entered_chatroom_at).filter(
                    timestamp__lt=self.before_last_read_time)[:30], many=True).data
            after_last_read = InquiryMessageSerializer(
                self.chatroom.messages.filter(timestamp__gte=self.this_participant.entered_chatroom_at).filter(
                    timestamp__gte=self.before_last_read_time), many=True).data

            messages = after_last_read + before_last_read
            self.loaded_cnt += len(messages)
            if len(before_last_read) and len(after_last_read) > 30:
                messages = after_last_read + [InquiryReadTillHereMessage] + before_last_read
            return messages
        else:
            return self.get_last_30_messages

    @database_sync_to_async
    def get_last_30_messages(self):
        messages = self.chatroom.messages.all()[self.loaded_cnt:self.loaded_cnt + 30]
        self.loaded_cnt += 30
        return InquiryMessageSerializer(messages, many=True).data

    @database_sync_to_async
    def update_participant_online(self):
        participant = self.participants.filter(is_inquirer=self.is_inquirer)
        if participant:
            participant.update(is_online=True)
            participant.update(unread_cnt=0)

    @database_sync_to_async
    def update_user_offline(self):
        InquiryChatParticipant.objects.filter(chatroom=self.chatroom, is_inquirer=self.is_inquirer).update(
            is_online=False)

    @database_sync_to_async
    def get_chatroom_and_participants_info(self):
        try:
            self.chatroom = InquiryChatRoom.objects.get(pk=self.chatroom_id)
            self.team_pk = self.chatroom.team.pk
            self.team_name = self.chatroom.team.name
            self.participants = InquiryChatParticipant.objects.filter(chatroom=self.chatroom)
            self.participants_set = {self.chatroom.inquirer.pk, self.chatroom.team.responder.pk}

            self.inquirer = self.chatroom.inquirer
            self.responder = self.chatroom.team.responder
            self.is_responder, self.is_inquirer, self.is_member = False, False, False
            if self.responder == self.user:
                self.is_responder = True
                self.this_participant = self.participants.get(is_inquirer=False)
            if self.inquirer == self.user:
                self.is_inquirer = True
                self.this_participant = self.participants.get(is_inquirer=True)
            self.is_member = self.chatroom.team.members.filter(pk=self.user.pk).exists()

            if self.this_participant is not None:
                self.before_last_read_time = self.this_participant.last_read_time.astimezone(
                    timezone.get_current_timezone())

            self.online_participants = []
            for participant in self.participants.filter(is_online=True):
                if participant.is_inquirer:
                    self.online_participants.append(self.inquirer.pk)
                else:
                    self.online_participants.append(self.responder.pk)
            self.alarm_on_participants = set([])
            for participant in self.participants.filter(alarm_on=True):
                if participant.is_inquirer:
                    self.alarm_on_participants.add(self.inquirer.pk)
                else:
                    self.alarm_on_participants.add(self.responder.pk)
            return True
        except Exception as e:
            print('Connection error:', e)
            return False

    @database_sync_to_async
    def participant_was_offline(self):
        if self.is_responder:
            return not self.participants.get(is_inquirer=False).is_online
        elif self.is_inquirer:
            return not self.participants.get(is_inquirer=True).is_online
        return None

    @database_sync_to_async
    def get_paricipants(self):
        return InquiryChatParticipant.objects.filter(chatroom=self.chatroom)

    @database_sync_to_async
    def is_inquirer_participant_exist(self, participants):
        return participants.filter(is_inquirer=True).exists()

    @database_sync_to_async
    def is_responder_participant_exist(self, participants):
        return participants.filter(is_inquirer=False).exists()
