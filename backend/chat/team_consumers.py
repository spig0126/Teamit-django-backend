import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import F
from channels.db import database_sync_to_async
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import *
from .serializers import *
from team.serializers import MyTeamMemberDetailSerializer
from fcm_notification.tasks import send_fcm_to_user_task


class TeamChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.before_last_read_time = None
        self.alarm_on_participants = None
        self.member_pk = None
        self.participant_cnt = None
        self.this_participant = None
        self.online_participants = None
        self.participants = None
        self.team_pk = None
        self.chatroom = None
        self.loaded_cnt = None
        self.last_read_time = None
        self.chatroom_name = None
        self.chatroom_id = None
        self.user = None

    async def connect(self):
        self.user = self.scope.get('user')
        self.chatroom_id = int(self.scope["url_route"]["kwargs"]["chatroom_id"])
        self.chatroom_name = f"team_chat_{self.chatroom_id}"
        self.last_read_time = None
        self.loaded_cnt = 0
        self.chatroom = None
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

    async def receive(self, text_data):
        data = json.loads(text_data)
        type = data["type"]
        message = data.get('message', None)

        if type == 'msg':
            await self.handle_message(message)
        elif type == 'history':
            await self.send_last_30_messages()
        elif type == 'enter':
            await self.handle_enter(message)
        elif type == 'exit':
            await self.handle_exit()
        elif type == 'settings':
            await self.handle_settings()
        elif type == 'update_alarm_status':
            await self.handle_update_alarm_status()
        elif type == 'update_chatroom_background':
            await self.handle_update_chatroom_background(message)
        elif type == 'update_chatroom_name':
            await self.handle_update_chatroom_name(message)
        elif type == "fetch_non_participants":
            await self.handle_fetch_non_participants()

    # ------------------handle related----------------------
    async def handle_update_alarm_status(self):
        new_alarm_status = await self.update_alarm_status()
        await self.send_group_message('alarm_change', {'user': self.user.pk, 'alarm_on': new_alarm_status})
        status_message = await self.create_status_message({'alarm_on': new_alarm_status})
        await self.send_user_status_this_message(status_message, [self.user.pk])

    async def handle_message(self, message):
        msg_details = {
            'chatroom': self.chatroom_id,
            'user': self.user.pk,
            'member': self.member_pk,
            'content': message['content']
        }
        message = await self.create_message(msg_details)
        await self.update_chatroom_last_msg(message['content'])
        await self.update_offline_participant_unread_cnt()
        await self.send_group_message('msg', message)
        await self.send_offline_participants_fcm(message)
        await self.send_user_status_new_message(message)

    async def handle_enter(self, message):
        announcement = {
            'chatroom': self.chatroom_id,
            'content': f'{message["name"]} / {message["position"]} 님이 입장했습니다',
            'is_msg': False
        }
        message = await self.create_message(announcement)
        await self.send_group_message('enter', message)

    async def handle_exit(self):
        await self.remove_this_participant_from_chatroom()
        await self.send_message('exit_successful', True)
        await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
        await self.close()

    async def handle_settings(self):
        background, name, participant_list, alarm_on = await self.get_settings_info()
        type = 'settings'
        message = {
            'background': background,
            'name': name,
            'participant_list': participant_list,
            'alarm_on': alarm_on
        }
        await self.send_message(type, message)

    async def handle_update_chatroom_background(self, new_background):
        await self.update_chatroom_background(new_background)
        status_message = await self.create_status_message({'background': new_background})
        await self.send_user_status_this_message(status_message, self.participants)

    async def handle_update_chatroom_name(self, new_name):
        await self.update_chatroom_name(new_name)
        status_message = await self.create_status_message({'name': new_name})
        await self.send_user_status_this_message(status_message, self.participants)

    async def handle_fetch_non_participants(self):
        non_participants = await self.get_non_participants()
        await self.send_message('non_participant_list', non_participants)

    # ------------------event related-----------------------
    async def online(self, event):
        user = event['message'].get('user', None)
        self.online_participants.append(user)
        await self.send_message(event['type'], event['message'])

    async def offline(self, event):
        user = event['message'].get('user', None)
        try:
            self.online_participants.remove(user)
        except Exception as e:
            pass
        await self.send_message(event['type'], event['message'])

    async def enter(self, event):
        await self.send_message('msg', event['message'])
        await self.update_participant_info()

    async def exit(self, event):
        await self.send_message('msg', event['message'])
        await self.update_participant_info()

    async def msg(self, event):
        await self.send_message(event['type'], event['message'])

    async def alarm_change(self, event):
        if event['message']['alarm_on']:
            self.alarm_on_participants.add(event['message']['user'])
        else:
            self.alarm_on_participants.discard(event['message']['user'])
        await self.send_message(event['type'], event['message'])

    # ------------------utility related-----------------------
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
            'chat_type': 'team',
            'message': status_message
        }
        channel_name = f'status_{self.user.pk}'
        await self.channel_layer.group_send(
            channel_name, message_info
        )

    async def send_offline_participants_fcm(self, message):
        title = self.chatroom.name
        body = message['content']
        data = {
            'page': 'chat',
            'chatroom_name': title,
            'chatroom_id': str(self.chatroom_id),
            'chat_type': 'team'
        }

        alarm_on_offline_participants = (set(self.participants) - set(self.online_participants)).intersection(
            self.alarm_on_participants)
        for participant in alarm_on_offline_participants:
            send_fcm_to_user_task.delay(participant, title, body, data)

    async def mark_as_online(self):
        # Alerts the frontend of 'online' status and updates participant info.

        data = {
            'user': self.user.pk,
            'last_read_time': self.last_read_time.isoformat()
        }
        await self.update_this_participant_online()
        await self.send_group_message('online', data)

    async def mark_as_offline(self):
        # Alerts others of the disconnect and updates participant info as offline.
        if self.chatroom is not None:
            await self.send_group_message('offline', {'user': self.user.pk})
            await self.update_this_participant_offline()

    async def join_chatroom(self):
        # Joins the chatroom group, accept connection, and sends the last 30 messages
        await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
        await self.accept()
        await self.send_is_alone_message()
        await self.send_recent_messages()

    async def send_message(self, type, message):
        await self.send(text_data=json.dumps({
            'type': type,
            'message': message
        }))

    async def send_group_message(self, type, message):
        await self.channel_layer.group_send(
            self.chatroom_name, {"type": type, "message": message}
        )

    async def send_recent_messages(self):
        message = await self.get_recent_messages()
        await self.send_message('history', message)

    async def send_last_30_messages(self):
        message = await self.get_last_30_messages()
        await self.send_message('history', message)

    async def send_is_alone_message(self):
        await self.send_message('is_alone', self.participant_cnt == 1)

    async def send_user_status_this_message(self, status_message, to_users):
        for user in to_users:
            await self.channel_layer.group_send(
                f'status_{user}',
                {
                    "type": "msg",
                    "chat_type": "team",
                    "team_id": self.team_pk,
                    "message": status_message
                }
            )

    async def send_user_status_new_message(self, message):
        status_message = await self.create_status_message({
            'last_msg': message['content'],
            'updated_at': message['timestamp']
        })

        for user in self.participants:
            status_message['update_unread_cnt'] = (user not in self.online_participants)
            await self.channel_layer.group_send(
                f'status_{user}',
                {
                    "type": "msg",
                    "chat_type": "team",
                    "team_id": self.team_pk,
                    "message": status_message}
            )

    async def create_status_message(self, updates):
        base = {
            'id': self.chatroom_id,
            'name': '',
            'avatar': '',
            'background': '',
            'last_msg': '',
            'updated_at': '',
            'update_unread_cnt': False,
            'alarm_on': None
        }
        status_message = {key: updates.get(key, base.get(key)) for key in base}
        return status_message

    # ------------------DB related-----------------------\
    @database_sync_to_async
    def get_non_participants(self):
        participating_member_pks = TeamMembers.objects.filter(participants__chatroom=self.chatroom).values('pk')
        non_participants = TeamMembers.objects.filter(team=self.chatroom.team).exclude(pk__in=participating_member_pks)
        return MyTeamMemberDetailSerializer(sorted(non_participants, key=lambda participant: participant.name),
                                            many=True).data

    @database_sync_to_async
    def update_chatroom_background(self, new_background):
        self.chatroom.background = new_background
        self.chatroom.save()

    @database_sync_to_async
    def update_chatroom_name(self, new_name):
        self.chatroom.name = new_name
        self.chatroom.save()

    @database_sync_to_async
    def update_alarm_status(self):
        self.this_participant.alarm_on = not self.this_participant.alarm_on
        self.this_participant.save()
        return self.this_participant.alarm_on

    @database_sync_to_async
    def get_settings_info(self):
        participants = (
            TeamChatParticipant.objects
                .filter(chatroom=self.chatroom, member__isnull=False)
                .select_related('member', 'user')
        )
        members = sorted([participant.member for participant in participants],
                         key=lambda member: (member.user != self.user, member.name))
        participant_list = MyTeamMemberDetailSerializer(members, many=True).data
        name = self.chatroom.name
        background = self.chatroom.background
        alarm_on = self.this_participant.alarm_on

        return background, name, participant_list, alarm_on

    @database_sync_to_async
    def remove_this_participant_from_chatroom(self):
        self.chatroom = None
        self.team_pk = None
        self.participants = None
        self.online_participants = None
        self.this_participant = None
        TeamChatParticipant.objects.get(user=self.user, chatroom=self.chatroom_id).delete()

    @database_sync_to_async
    @transaction.atomic
    def update_offline_participant_unread_cnt(self):
        TeamChatParticipant.objects.filter(chatroom=self.chatroom_id, is_online=False).exclude(user=self.user).update(
            unread_cnt=F('unread_cnt') + 1)

    @database_sync_to_async
    def update_participant_info(self):
        participants = TeamChatParticipant.objects.filter(chatroom=self.chatroom)
        self.participant_cnt = participants.count()
        self.participants = list(participants.values_list('user', flat=True))
        self.online_participants = list(participants.filter(is_online=True).values_list('user', flat=True))

    @database_sync_to_async
    @transaction.atomic
    def create_message(self, data):
        try:
            serializer = TeamMessageCreateSerialzier(data=data)
            serializer.is_valid(raise_exception=True)

            instance = serializer.save()
            unread_cnt = 0 if not instance.is_msg else self.participant_cnt - len(set(self.online_participants))
            return TeamMessageSerializer(instance, context={'unread_cnt': unread_cnt}).data
        except ValidationError as e:
            self.send_message('error', e.detail)

    @database_sync_to_async
    def get_chatroom_and_participants_info(self):
        '''
        - get's chatroom and its participant info from DB
        - checks if user is particpant of this chatroom
        '''
        try:
            self.chatroom = TeamChatRoom.objects.get(id=self.chatroom_id)
            self.team_pk = self.chatroom.team.pk
            participants = TeamChatParticipant.objects.filter(chatroom=self.chatroom)
            self.participant_cnt = participants.count()
            self.participants = list(participants.values_list('user', flat=True))
            self.online_participants = list(participants.filter(is_online=True).values_list('user', flat=True))
            self.this_participant = participants.get(user=self.user)
            self.member_pk = self.this_participant.member.pk
            self.last_read_time = self.this_participant.last_read_time.astimezone(timezone.get_current_timezone())
            self.before_last_read_time = self.last_read_time
            self.alarm_on_participants = set(participants.filter(alarm_on=True).values_list('user', flat=True))
            return True
        except:
            return False

    @database_sync_to_async
    def this_participant_was_offline(self):
        return not self.this_participant.is_online

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
        self.this_participant.is_online = False
        self.this_participant.save()

    @database_sync_to_async
    def get_recent_messages(self):
        before_last_read = TeamMessageSerializer(
            self.chatroom.messages.filter(timestamp__gte=self.this_participant.entered_chatroom_at).filter(
                timestamp__lt=self.before_last_read_time)[:30], many=True).data
        after_last_read = TeamMessageSerializer(
            self.chatroom.messages.filter(timestamp__gte=self.this_participant.entered_chatroom_at).filter(
                timestamp__gte=self.before_last_read_time), many=True).data

        messages = after_last_read + before_last_read
        self.loaded_cnt += len(messages)
        if len(before_last_read) and len(after_last_read) > 30:
            messages = after_last_read + [TeamReadTillHereMessage] + before_last_read

        return messages

    @database_sync_to_async
    def get_last_30_messages(self):
        messages = self.chatroom.messages.filter(timestamp__gte=self.this_participant.entered_chatroom_at).all()[
                   self.loaded_cnt:self.loaded_cnt + 30]
        self.loaded_cnt += 30
        return TeamMessageSerializer(messages, many=True).data

    @database_sync_to_async
    def update_chatroom_last_msg(self, last_msg):
        self.chatroom.last_msg = last_msg
        self.chatroom.save()
