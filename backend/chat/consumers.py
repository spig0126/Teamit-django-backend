import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Sum, F
from channels.db import database_sync_to_async
from datetime import datetime
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import *
from team.models import TeamPermission
from .serializers import*

class PrivateChatConsumer(AsyncWebsocketConsumer):
     async def connect(self):
          self.user = self.scope.get('user')
          self.chatroom_id = self.scope["url_route"]["kwargs"]["chatroom_id"]
          self.chatroom_name = f"private_chat_{self.chatroom_id}"
          self.chatroom = await self.get_chatroom()
          self.participant = await self.get_participant()
          self.last_read_time = await self.get_last_read_time()
          self.loaded_cnt = 0
          
          if self.participant:
               # if user offline -> online, update former messages' unread_cnt 
               await self.get_offline_participants()
               if self.user.pk in self.offline_participants:
                    await self.channel_layer.group_send(
                         self.chatroom_name,
                         {
                              'type': 'online',
                              'message': {
                                   'user': self.user.pk,
                                   'last_read_time': self.last_read_time
                              }
                         }
                    )
               await self.update_user_as_online()
               
               # join/connect chatroom
               await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
               await self.accept()
               
               # send history
               await self.send_last_30_messages()

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

          # Send message to WebSocket
          await self.send(text_data=json.dumps({"message": message}))
     
     #----------------EVENT RELATED------------------------------------
     async def online(self, event):
          online_user_pk = event['messages']['user']
          last_read_time = event['messages']['last_read_time']
          self.offline_participants.discard(online_user_pk)
          await self.send_message(event['type'], last_read_time)
          
     async def offline(self, event):
          offline_user_pk = event['messages']['user']
          last_read_time = event['messages']['last_read_time']
          self.offline_participants.discard(offline_user_pk)
          await self.send_message(event['type'], last_read_time)
          
          
     #----------------UTILITY FUNCTIONS---------------------------------
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
          
     async def send_last_30_messages(self):
          message = await self.get_last_30_messages()
          await self.send_message('history', message)
          
     #----------------DATABASE RELATED------------------------------------
     @database_sync_to_async
     def get_last_30_messages(self):
          offline_users_last_read_time = (PrivateChatParticipant.objects
                                             .filter(chatroom=self.chatrrom_id, is_online=False)
                                             .values_list('last_read_time', flat=True))
          messages = self.chatroom.messages.all()[self.loaded_cnt: self.loaded_cnt + 30]
          self.loaded_cnt += 30
          return PrivateMessageSerializer(messages, many=True, context={'offline_users_last_read_time': offline_users_last_read_time}).data
     
     @database_sync_to_async
     def get_offline_participants(self):
          self.offline_participants = set(self.chatroom.participants.filter(is_online=False).values_list('pk', flat=True))
          
     @database_sync_to_async
     @transaction.atomic
     def update_user_as_online(self):
          self.participant.is_online = True
          self.participant.unread_cnt = 0
          self.last_unread_time = datetime.now()
          self.participant.save()
          self.offline_participants.discard(self.user.pk)
     
     @database_sync_to_async
     def get_last_read_time(self):
          return self.participant.last_read_time.isoformat()
     
     @database_sync_to_async
     def get_participant(self):
          try:
               return PrivateChatParticipant.objects.get(chatroom=self.chatroom, user=self.user)
          except PrivateChatParticipant.DoesNotExist:
               return None
     
     @database_sync_to_async
     def get_chatroom(self):
          try:
               return PrivateChatRoom.objects.get(id=self.chatroom_id)
          except PrivateChatRoom.DoesNotExist:
               return None



################################################
class TeamChatConsumer2(AsyncWebsocketConsumer):
     async def connect(self):
          self.user = self.scope.get('user')
          self.chatroom_id = self.scope["url_route"]["kwargs"]["chatroom_id"]
          self.chatroom_name = f"team_chat_{self.chatroom_id}"
          self.last_read_time = None
          self.loaded_cnt = 0
          
          is_valid = await self.get_chatroom_and_participants_info()
          if not is_valid:
               await self.close(code=4001)
               return
          
          was_offline = await self.this_participant_was_offline()
          if was_offline:
               await self.mark_as_online()
          
          await self.join_chatroom()

     async def disconnect(self, close_code):
          await self.mark_as_offline()
          await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
     
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
               await self.handle_exit(message)
     
     #------------------handle related----------------------
     async def handle_message(self, message):
          msg_details = {
               'chatroom': self.chatroom_id,
               'user': self.user.pk,
               'member': self.member_pk,
               'content': message['content']
          }
          message = await self.create_message(msg_details)
          self.chatroom.last_msg = message['content']
          self.update_chatroom()
          
          await self.send_group_message('msg', message)
          await self.send_user_status_message(message)
          await self.update_offline_participant_unread_cnt()
     
     async def handle_enter(self, message):
          announcement = {
               'chatroom': self.chatroom_id,
               'content': f'{message["name"]} / {message["position"]} 님이 입장했습니다',
               'is_msg': False
          }
          message = await self.create_message(announcement)
          await self.send_group_message('enter', message)
     
     async def handle_exit(self, message):
          await self.remove_this_participant_from_chatroom()
          await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
          
          announcement = {
               'chatroom': self.chatroom_id,
               'content': f'{message["name"]} / {message["position"]} 님이 퇴장했습니다',
               'is_msg': False
          }
          message = await self.create_message(announcement)
          await self.send_group_message('exit', message)
          await self.close(code=1000)
          
          
     #------------------event related-----------------------
     async def online(self, event):
          user = event['message'].get('user', None)
          self.online_participants.append(user)
          print('online', self.user, user)
          print(self.online_participants)
          await self.send_message(event['type'], event['message'])


     async def offline(self, event):
          # remove user from online_participants
          user = event['message'].get('user', None)
          try:
               self.online_participants.remove(user)
          except ValueError:
               pass
          print('exit', self.user, user)
          print(self.online_participants)

     async def enter(self, event):
          await self.send_message('msg', event['message'])
          await self.update_participant_info()
     
     async def exit(self, event):
          await self.send_message('msg', event['message'])
          await self.update_participant_info()
     
     async def msg(self, event):
          await self.send_message(event['type'], event['message'])
          
     #------------------utility related-----------------------
     async def mark_as_online(self):
          '''
          Alerts the frontend of 'online' status and updates participant info.
          '''
          print(self.last_read_time)
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
          await self.send_group_message('offline', {'user': self.user.pk})
          await self.update_this_participant_offline()
               
     async def join_chatroom(self):
          '''
          Joins the chatroom group, accept connection, and sends the last 30 messages
          '''
          await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
          await self.accept()
          await self.send_last_30_messages()
          
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
     
     async def send_group_message(self, type, message):
          await self.channel_layer.group_send(
                    self.chatroom_name, {"type": type, "message": message}
               )
     
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
               'alarm_on': self.this_participant.alarm_on
          }
          
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
               
               
     #------------------DB related-----------------------
     @database_sync_to_async
     def remove_this_participant_from_chatroom(self):
          self.this_participant.delete()
          print(TeamChatParticipant.objects.filter(user=self.user.pk, chatroom=self.chatroom_id))
     
     @database_sync_to_async
     @transaction.atomic
     def update_offline_participant_unread_cnt(self):
          TeamChatParticipant.objects.filter(chatroom=self.chatroom_id, is_online=False).update(unread_cnt=F('unread_cnt')+1)
     
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
          
          self.last_read_time = self.this_participant.last_read_time
          
          self.online_participants.append(self.user.pk)
          print('update_this_participant_online')
     
     @database_sync_to_async
     def update_this_participant_offline(self):
          try:
               self.online_participants.remove(self.user.pk)
          except ValueError:
               pass
          try:
               if self.user not in self.online_participants:
                    self.this_participant.is_online = False
                    self.this_participant.save()
          except:
               pass
          
     @database_sync_to_async
     def get_last_30_messages(self):
          last_read_time_list = TeamChatParticipant.objects.filter(chatroom=self.chatroom_id, is_online=False).values_list('last_read_time', flat=True)
          messages = self.chatroom.messages.all()[self.loaded_cnt:self.loaded_cnt+30]
          self.loaded_cnt += 30
          return TeamMessageSerializer(messages, many=True, context={"last_read_time_list": last_read_time_list}).data
     
     @database_sync_to_async
     def update_chatroom(self):
          return self.chatroom.save()
     
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
               if not self.participant.is_online:
                    # update former messages' unread_cnt
                    await self.channel_layer.group_send(
                         self.chatroom_name, {
                              'type': 'online', 
                              'message': {
                                   'user': self.user.pk,
                                   'last_read_time': self.last_read_time.isoformat()
                              }})
               # update user's unread, is_online status
               self.participant.unread_cnt = 0
               self.participant.is_online = True
               self.last_read_time = self.participant.last_read_time
               await self.update_participant()
               
               # get offline participants
               self.offline_participants = await self.get_offline_participants()
               print(self.offline_participants)

               
               
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
               
               instance = serializer.save()
               return TeamMessageSerializer(instance, context={'unread_cnt': len(set(self.offline_participants))}).data
          except ValidationError as e:
               self.send_message('error', e.detail)
     
     @database_sync_to_async
     def get_participants_info(self):
          participants = TeamChatParticipant.objects.filter(chatroom=self.chatroom_id)
          self.participant_cnt = participants.count()
          self.online_participant_list = list(participants.filter(is_online=True).values_list('user', flat=True))
          self.participant_list = list(participants.values_list('user', flat=True))

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
     def get_unread_cnt(self):
          private_unread_cnt = PrivateChatParticipant.objects.filter(user=self.user).aggregate(private_unread_cnt=Sum('unread_cnt'))['private_unread_cnt'] or 0
          team_unread_cnt = TeamChatParticipant.objects.filter(user=self.user, member__isnull=False).aggregate(team_unread_cnt=Sum('unread_cnt'))['team_unread_cnt'] or 0
          inquirer_unread_cnt = InquiryChatRoom.objects.filter(inquirer=self.user).aggregate(inquirer_unread_cnt=Sum('inquirer_unread_cnt'))['inquirer_unread_cnt'] or 0
          responder_unread_cnt = InquiryChatRoom.objects.filter(team__permission__responder=self.user).aggregate(responder_unread_cnt=Sum('responder_unread_cnt'))['responder_unread_cnt'] or 0
          
          unread_cnt = {
               'all': private_unread_cnt + team_unread_cnt + inquirer_unread_cnt + responder_unread_cnt,
               'private': private_unread_cnt,
               'team': team_unread_cnt,
               'inquiry': inquirer_unread_cnt + responder_unread_cnt
          }
          return unread_cnt
     
     @database_sync_to_async
     @transaction.atomic
     def remove_user_from_chatroom(self, chat_type, chatroom_id):
          if chat_type == 'private':
               participant = PrivateChatParticipant.objects.get(user=self.user, chatroom=chatroom_id)
               participant_name = participant.name
               participant.delete()
               return participant_name, None
          if chat_type == 'team':
               participant = TeamChatParticipant.objects.get(user=self.user, chatroom=chatroom_id)
               participant_name = participant.name
               participant_position = participant.position
               participant.delete()
               return participant_name, participant_position
          if chat_type == 'inquiry':
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
     def create_message(self, chat_type, data):
          if chat_type == 'private':
               pass
          if chat_type == 'team':
               try:
                    serializer = TeamMessageCreateSerialzier(data=data)
                    serializer.is_valid(raise_exception=True)
                    instance = serializer.save()
                    return TeamMessageSerializer(instance, context={'unread_cnt': None}).data
               except ValidationError as e:
                    self.send_message('error', e.detail)
          if chat_type == 'inquiry':
               pass
     
     commands = {
          'fetch_private_chatrooms': fetch_private_chatrooms,
          'fetch_inquiry_chatrooms': fetch_inquiry_chatrooms,
          'fetch_team_chatrooms': fetch_team_chatrooms,
          'update_private_chatroom_alarm': update_private_chatroom_alarm,
          'update_inquiry_chatroom_alarm': update_inquiry_chatroom_alarm,
          'update_team_chatroom_alarm': update_team_chatroom_alarm,
     }


     async def connect(self):
          self.user = self.scope.get('user')
          self.user_id = self.user.id
          self.name = f'status_{self.user_id}'
          self.chat_type = 'all'
          self.team_id = 0
          self.filter = 'all'
          self.unread_cnt = await self.get_unread_cnt()

          await self.channel_layer.group_add(self.name, self.channel_name)
          await self.accept()
          
     async def disconnect(self, close_code):
          await self.channel_layer.group_discard(self.name, self.channel_name)
          await self.close(code=close_code)

     async def receive(self, text_data):
          try:
               data = json.loads(text_data)
          except json.JSONDecodeError:
               await self.close()
          
          msg_type = data.get("type")
          
          if msg_type == 'change':
               await self.handle_change(data)
          elif msg_type == 'udpate_alarm_status':
               await self.handl_update_alarm_status(data)
          elif msg_type == 'exit':
               await self.handle_exit(data)
     
     #-------------------handle reltaed--------------------------
     async def handle_change(self, data):
          self.chat_type = data.get("chat_type", self.chat_type)
          self.team_id = data.get("team_id", self.team_id)
          self.filter = data.get("filter", self.team_id)
          
          if self.chat_type == 'all':
               await self.send_message('update_total_unread_cnt', {'cnt': self.unread_cnt['all']})
          else:
               await self.send_chatroom_list(self.chat_type)

     async def handl_update_alarm_status(self, data):
          chat_type = data.get('chat_type')
          chatroom_id = data.get('chatroom_id')
          if chat_type and chatroom_id:
               await self.commands[f'update_{chat_type}_chatroom_alarm'](self, chatroom_id)
     
     async def handle_exit(self, data):
          chat_type = data.get('chat_type')
          chatroom_id = data.get('chatroom_id')
          if chat_type and chatroom_id:
               # create exit message
               name, position = await self.remove_user_from_chatroom(chat_type, chatroom_id)
               data = {
                    'chatroom': chatroom_id,
                    'content': f'{name} / {position} 님이 퇴장했습니다' if position else f'{name} 님이 퇴장했습니다',
                    'is_msg': False
               }
               message = await self.create_message(chat_type, data)
               
               # send message to group
               chatroom_name = f'{chat_type}_chat_{chatroom_id}'
               await self.channel_layer.group_send(
                    chatroom_name, {"type": "msg", "message": message}
               )
               await self.close()
     
     #-------------------event related----------------------------
     async def msg(self, event):
          chat_type = event['chat_type']
          message = event['message']
          team_id = event.get('team_id', self.team_id)
          filter = event.get('filter', self.filter)
          
          await self.update_unread_cnt(chat_type)
     
          if self.chat_type == 'all':
               await self.send_message('update_total_unread_cnt', {'cnt': self.unread_cnt['all']})
          elif self.chat_type == chat_type and self.team_id == team_id and self.filter == filter:
               await self.send_message('update_chatroom', message)
               
     #--------------------utiity related---------------------------------       
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
     
     async def send_chatroom_list(self, chat_type):
          type = f'{chat_type}_chatroom_list'
          message = await self.commands[f'fetch_{chat_type}_chatrooms'](self)
          await self.send_message(type, message)
     
     async def update_unread_cnt(self, chat_type):
          self.unread_cnt['all'] += 1
          self.unread_cnt[chat_type] += 1
          if self.chat_type != 'all':
               await self.send_message(f'update_{chat_type}_unread_cnt', {'cnt': self.unread_cnt[chat_type]})