import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Sum, F
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import *
from team.models import TeamPermission
from .serializers import*

class PrivateChatConsumer(AsyncWebsocketConsumer):
     async def connect(self):
          self.user = self.scope.get('user')
          self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
          self.room_name = f"private_chat_{self.room_id}"
          
          if self.user and self.user_is_participant():
               # Join room group
               await self.channel_layer.group_add(self.room_name, self.channel_name)
               await self.accept()
          else:
               await self.close()

     async def disconnect(self, close_code):
          # Leave room group
          await self.channel_layer.group_discard(self.room_name, self.channel_name)

     # Receive message from WebSocket (frontend -> channel)
     async def receive(self, text_data):
          text_data_json = json.loads(text_data)
          type = text_data_json["type"]
          message = text_data_json["message"]

          if type == 'private_chat.leave':
               await self.channel_layer.group_send(
                    self.room_name, {"type": "private_chat.message", "message": message}
               )
          # Send message to room group
          await self.channel_layer.group_send(
               self.room_name, {"type": "private_chat.message", "message": message}
          )

     # Receive message from room group (channel -> frontend)
     async def private_chat_message(self, event):
          message = event["message"]
          print(event)

          # Send message to WebSocket
          await self.send(text_data=json.dumps({"message": message}))
     
     @sync_to_async
     def user_is_participant(self):
          try:
               chatroom = PrivateChatRoom.objects.prefetch_related('participants').get(id=self.room_id)
               if chatroom.participants.filter(id=self.user.id).exists():
                    return True
          except:
               return False
     
     @sync_to_async
     def get_room(self, room_id):
          try:
               return PrivateChatRoom.objects.get(id=room_id)
          except PrivateChatRoom.DoesNotExist:
               pass

################################################################
class TeamChatConsumer(AsyncWebsocketConsumer):
     async def connect(self):
          self.user = self.scope.get('user')
          self.chatroom_id = self.scope["url_route"]["kwargs"]["chatroom_id"]
          self.chatroom_name = f"team_chat_{self.chatroom_id}"
          self.chatroom = await self.get_chatroom(self.chatroom_id)
          self.chatroom_participants = await self.get_chatroom_participants()
          self.participant = await self.get_participant()
          self.member_pk = await self.get_member_pk()
          self.loaded_cnt = 0
          self.offline_participants = set()
          self.last_read_time = None
          
          if self.participant is not None:
               # update user's unread, is_online status
               self.participant.unread_cnt = 0
               self.participant.is_online = True
               self.last_read_time = self.participant.last_read_time
               await self.update_participant()
               
               # get offline participants
               self.offline_participants = await self.get_offline_participants()
               print(self.offline_participants)

               # update former messages' unread_cnt
               await self.channel_layer.group_send(
                    self.chatroom_name, {
                         'type': 'online', 
                         'message': {
                              'user': self.user.pk,
                              'last_read_time': self.last_read_time.isoformat()
                         }})
               
               # Join room group
               await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
               await self.accept()
               await self.send_last_30_messages()
          else:
               await self.close()

     async def disconnect(self, close_code):
          self.participant.is_online = False
          await self.update_participant()
          await self.channel_layer.group_send(
                    self.chatroom_name, {
                         'type': 'offline', 
                         'message': {
                              'user': self.user.pk,
                              'last_read_time': self.last_read_time.isoformat()
                         }})
               
          # Leave room group
          await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)

     # Receive message from WebSocket (frontend -> channel)
     async def receive(self, text_data):
          data = json.loads(text_data)
          type = data["type"]
          message = data.get('message', None)

          if type == 'msg':
               # create message in db
               message['chatroom'] = self.chatroom_id
               message['user'] = self.user.pk
               message['member'] = self.member_pk
               message = await self.create_message(message)

               # udpate chatroom's last msg
               self.chatroom.last_msg = message['content']
               self.update_chatroom()
               
               # send msg to group
               await self.channel_layer.group_send(
                    self.chatroom_name, {"type": "msg", "message": message}
               )
               
               # alert users' ChatStatusConsumer
               await self.send_user_status_message(message)
               
               # update offline user's unread_cnt for chatroom
               await self.update_offline_participant_unread_cnt()
          elif type == 'history':
               await self.send_last_30_messages()
          elif type == 'enter':
               data = {
                    'chatroom': self.chatroom_id,
                    'content': f'{message["name"]} / {message["position"]} 님이 입장했습니다',
                    'is_msg': False
               }
               message = await self.create_message(data)
               
               # send msg to group
               await self.channel_layer.group_send(
                    self.chatroom_name, {"type": "msg", "message": message}
               )
          elif type == 'exit':
               data = {
                    'chatroom': self.chatroom_id,
                    'content': f'{message["name"]} / {message["position"]} 님이 퇴장했습니다',
                    'is_msg': False
               }
               message = await self.create_message(data)
               
               # send msg to group
               await self.channel_layer.group_send(
                    self.chatroom_name, {"type": "msg", "message": message}
               )
          else:   
               pass

     ####################################################
     # event related functions
     async def online(self, event):
          new_online_user = event["message"]["user"]
          if new_online_user in self.offline_participants:
               self.offline_participants.remove(new_online_user)
               await self.send_message(event['type'], event['message'])
          print("online", self.user, print(self.offline_participants))
     
     async def offline(self, event):
          new_offline_user = event["message"]["user"]
          try:
               self.offline_participants.append(new_offline_user)
          except:
               pass
          print("offline", self.user, print(self.offline_participants))
     
     async def msg(self, event):
          await self.send_message(event['type'], event['message'])
     
     async def enter(self, event):
          await self.send_message('msg', event['message'])
          self.chatroom_participants = await self.get_chatroom_participants()
     
     async def exit(self, event):
          await self.send_message('msg', event['message'])
          self.chatroom_participants = await self.get_chatroom_participants()
          
          
     #################################################
     # internal functions
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
     
     async def send_last_30_messages(self):
          message = await self.get_last_30_messages()
          await self.send_message('history', message)
     
     async def send_user_status_message(self, message):
          status_message = {
               'id': self.chatroom_id,
               'name': self.chatroom.name,
               'avatar': '',
               'background': self.chatroom.background,
               'last_msg': message['content'],
               'updated_at': message['timestamp'],
               'alarm_on': self.participant.alarm_on
          }
          
          for participant in self.chatroom_participants:
               status_message['update_unread_cnt'] = (participant["user"] in self.offline_participants)
               await self.channel_layer.group_send(
                    f'status_{participant["user"]}',
                    {
                         "type": "msg", 
                         "chat_type": "team", 
                         "tead_id": await self.get_team_pk(),
                         "message": status_message}
               )
          
     #################################################
     # database access functions
     @database_sync_to_async
     @transaction.atomic
     def update_offline_participant_unread_cnt(self):
          TeamChatParticipant.objects.filter(chatroom=self.chatroom_id, user__in=self.offline_participants).update(unread_cnt=F('unread_cnt')+1)
     
     @database_sync_to_async
     @transaction.atomic
     def create_message(self, data):
          try:
               serializer = TeamMessageCreateSerialzier(data=data)
               serializer.is_valid(raise_exception=True)
               print(serializer)
               
               instance = serializer.save()
               return TeamMessageSerializer(instance, context={'unread_cnt': len(set(self.offline_participants))}).data
          except ValidationError as e:
               self.send_message('error', e.detail)
               
     @database_sync_to_async
     def get_chatroom_participants(self):
          return list(TeamChatParticipant.objects.filter(chatroom=self.chatroom_id).values('pk', 'user'))
     
     @database_sync_to_async
     def get_participant(self):
          try:
               return TeamChatParticipant.objects.get(user=self.user, chatroom=self.chatroom_id)
          except:
               return None
     
     @database_sync_to_async
     def get_member_pk(self):
          try:
               return self.participant.member.pk
          except:
               return None
     
     @database_sync_to_async
     def get_chatroom(self, chatroom_id):
          try:
               return TeamChatRoom.objects.get(id=chatroom_id)
          except TeamChatRoom.DoesNotExist:
               return None
     
     @database_sync_to_async
     def get_team_pk(self):
          return self.chatroom.team.pk
     
     @database_sync_to_async
     def get_last_30_messages(self):
          last_read_time_list = TeamChatParticipant.objects.filter(chatroom=self.chatroom_id, is_online=False).values_list('last_read_time', flat=True)
          messages = self.chatroom.messages.all()[self.loaded_cnt:self.loaded_cnt+30]
          self.loaded_cnt += 30
          return TeamMessageSerializer(messages, many=True, context={"last_read_time_list": last_read_time_list}).data
     
     @database_sync_to_async
     def get_offline_participants(self):
          return list(TeamChatParticipant.objects.filter(
                    chatroom=self.chatroom_id, 
                    is_online=False
               ).values_list('user', flat=True))
          
     @database_sync_to_async
     def update_participant(self):
          return self.participant.save()
     
     @database_sync_to_async
     def update_chatroom(self):
          return self.chatroom.save()

######################################################################
class ChatStatusConsumer(AsyncWebsocketConsumer):
     # DB related functions
     @database_sync_to_async
     def fetch_private_chatrooms(self):
          blocked_users = self.user.blocked_users.values('pk')
          private_chatrooms = PrivateChatParticipant.objects.filter(
                    user=self.user
               ).exclude(
                    chatroom__participants__in=blocked_users
               ).distinct()
          return MyPrivateChatRoomDetailSerializer(private_chatrooms, many=True).data

     @database_sync_to_async
     def fetch_inquiry_chatrooms(self):
          responder_rooms = InquiryChatRoom.objects.filter(team__permission__responder=self.user)
          inquirer_rooms = InquiryChatRoom.objects.filter(inquirer=self.user)
          responder_room_list = InquiryChatRoomDetailSerializer(responder_rooms, many=True, context={'type': 'responder'}).data
          inquirer_room_list = InquiryChatRoomDetailSerializer(inquirer_rooms, many=True, context={'type': 'inquirer'}).data
          return responder_room_list + inquirer_room_list

     @database_sync_to_async
     def fetch_team_chatrooms(self):
          team_chatrooms = TeamChatRoom.objects.filter(team__pk=self.team_id, participants=self.user)
          return TeamChatRoomDetailSerializer(team_chatrooms, many=True, context={'user': self.user}).data

     @database_sync_to_async
     def update_private_chatroom_alarm(self, chatroom_id):
          instance = PrivateChatParticipant.objects.filter(user=self.user, chatroom=chatroom_id).first()
          instance.alarm_on = not instance.alarm_on
          instance.save()
          
     @database_sync_to_async
     def update_inquiry_chatroom_alarm(self, chatroom_id):
          instance = InquiryChatRoom.objects.get(id=chatroom_id)
          type = 'inquirer'
          if self.user == instance.inquirer:
               instance.inquirer_alarm_on = not instance.inquirer_alarm_on
          else:
               type = 'responder'
               instance.responder_alarm_on = not instance.responder_alarm_on
          instance.save()
     
     @database_sync_to_async
     def update_team_chatroom_alarm(self, chatroom_id):
          instance = TeamChatParticipant.objects.filter(user=self.user, chatroom=chatroom_id).first()
          instance.alarm_on = not instance.alarm_on
          instance.save()
     
     @database_sync_to_async
     def get_total_unread_cnt(self):
          private_unread_cnt = PrivateChatParticipant.objects.filter(user=self.user).aggregate(private_unread_cnt=Sum('unread_cnt'))['private_unread_cnt'] or 0
          team_unread_cnt = TeamChatParticipant.objects.filter(user=self.user, member__isnull=False).aggregate(team_unread_cnt=Sum('unread_cnt'))['team_unread_cnt'] or 0
          inquirer_unread_cnt = InquiryChatRoom.objects.filter(inquirer=self.user).aggregate(inquirer_unread_cnt=Sum('inquirer_unread_cnt'))['inquirer_unread_cnt'] or 0
          responder_unread_cnt = InquiryChatRoom.objects.filter(team__permission__responder=self.user).aggregate(responder_unread_cnt=Sum('responder_unread_cnt'))['responder_unread_cnt'] or 0
          
          return private_unread_cnt + team_unread_cnt + inquirer_unread_cnt + responder_unread_cnt
     
     @database_sync_to_async
     @transaction.atomic
     def remove_user_from_chatroom(self, chatroom_type, chatroom_id):
          if chatroom_type == 'private':
               participant = PrivateChatParticipant.objects.get(user=self.user, chatroom=chatroom_id)
               participant_name = participant.name
               participant.delete()
               return participant_name, None
          if chatroom_type == 'team':
               participant = TeamChatParticipant.objects.get(user=self.user, chatroom=chatroom_id)
               participant_name = participant.name
               participant_position = participant.position
               participant.delete()
               return participant_name, participant_position
          if chatroom_type == 'inquiry':
               chatroom = InquiryChatRoom.objects.get(chatroom=chatroom_id)
               participant_name = ''
               if chatroom.inquirer == self.user:
                    participant_name = chatroom.inquirer.name
                    chatroom.inquirer = None
               else:
                    participant_name = chatroom.team.name
                    chatroom.team = None
               chatroom.save()
               return participant_name, None
          
     @database_sync_to_async
     @transaction.atomic
     def create_message(self, chatroom_type, data):
          if chatroom_type == 'private':
               pass
          if chatroom_type == 'team':
               try:
                    serializer = TeamMessageCreateSerialzier(data=data)
                    serializer.is_valid(raise_exception=True)
                    instance = serializer.save()
                    return TeamMessageSerializer(instance, context={'unread_cnt': None}).data
               except ValidationError as e:
                    self.send_message('error', e.detail)
          if chatroom_type == 'inquiry':
               pass
     
     commands = {
          'fetch_private_chatrooms': fetch_private_chatrooms,
          'fetch_inquiry_chatrooms': fetch_inquiry_chatrooms,
          'fetch_team_chatrooms': fetch_team_chatrooms,
          'update_private_chatroom_alarm': update_private_chatroom_alarm,
          'update_inquiry_chatroom_alarm': update_inquiry_chatroom_alarm,
          'update_team_chatroom_alarm': update_team_chatroom_alarm,
     }
     
     async def send_chatroom_list(self, chatroom_type):
          type = f'{chatroom_type}_chatroom_list'
          message = await self.commands[f'fetch_{chatroom_type}_chatrooms'](self)
          await self.send_message(type, message)

     async def send_total_unread_cnt(self):
          type = 'total_unread_cnt'
          message = await self.get_total_unread_cnt()
          await self.send_message(type, message)

     async def exit(self, chatroom_type, chatroom_id):
          # create exit message
          name, position = await self.remove_user_from_chatroom(chatroom_type, chatroom_id)
          data = {
               'chatroom': chatroom_id,
               'content': f'{name} / {position} 님이 퇴장했습니다' if position else f'{name} 님이 퇴장했습니다',
               'is_msg': False
          }
          message = await self.create_message(chatroom_type, data)
          
          # send message to group
          chatroom_name = f'{chatroom_type}_chat_{chatroom_id}'
          await self.channel_layer.group_send(
               chatroom_name, {"type": "msg", "message": message}
          )

     async def connect(self):
          self.user = self.scope.get('user')
          self.user_id = self.user.id
          self.name = f'status_{self.user_id}'
          self.chat_type = 'all'
          self.team_id = 0
          self.filter = 'all'
          self.total_unread_cnt = 0
          
          await self.channel_layer.group_add(self.name, self.channel_name)
          await self.accept()
          
     async def disconnect(self, close_code):
          await self.channel_layer.group_discard(self.name, self.channel_name)
          await self.close(code=close_code)

     async def receive(self, text_data):
          data = json.loads(text_data)
          type = data["type"]
          if type == 'change':
               self.chat_type = data.get("chat_type", self.chat_type)
               self.team_id = data.get("team_id", self.team_id)
               self.filter = data.get("filter", self.team_id)
               if self.chat_type == 'all':
                    self.total_unread_cnt = await self.get_total_unread_cnt()
                    await self.send_message('update_total_unread_cnt', {'cnt': self.total_unread_cnt})
               else:
                    await self.send_chatroom_list(self.chat_type)
          elif type == 'udpate_alarm_status':
               await self.commands[f'update_{data["chat_type"]}_chatroom_alarm'](self, data["chatroom_id"])
          elif type == 'get_total_unread_cnt':
               await self.send_total_unread_cnt()
          elif type == 'exit':
               await self.exit(data['chat_type'], data['chatroom_id'])
     
     async def msg(self, event):
          chat_type = event['chat_type']
          message = event['message']
          self.total_unread_cnt += 1
     
          if self.chat_type == 'all':
               await self.send_message('update_total_unread_cnt', {'cnt': self.total_unread_cnt})
          elif self.chat_type == chat_type:
               # team_id, filter 에 대해서 더하기
               await self.send_message('update_chatroom', message)
               
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
     
