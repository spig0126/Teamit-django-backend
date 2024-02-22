import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import *
from .serializers import*
from user.serializers import UserSimpleDetailSerializer

class PrivateChatConsumer(AsyncWebsocketConsumer):
     async def connect(self):
          self.user = self.scope.get('user')
          self.chatroom_id = int(self.scope["url_route"]["kwargs"]["chatroom_id"])
          self.chatroom_name = f"private_chat_{self.chatroom_id}"
          self.online_participants = []
          self.loaded_cnt = 0
          
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
          await self.send_user_status_reset_message(self)
          await self.mark_as_offline()
          await self.close()
          
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
               await self.handle_udpate_chatroom_name(message)
          
     #---------------------handle related---------------
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
          
     async def handle_exit(self):
          chatroom_active = await self.remove_this_participant_from_chatroom()
          if not chatroom_active:
               await self.delete_chatroom()
          else:
               await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)

               announcement = {
                    'chatroom': self.chatroom_id,
                    'content': f'{self.user.name} 님이 퇴장했습니다',
                    'is_msg': False
               }
               message = await self.create_message(announcement)
               await self.send_group_message('exit', message)
          await self.close()
     
     async def handle_settings(self):
          participant_list =  await self.get_participant_list()
          if participant_list[0]['id'] != self.user.pk:
               participant_list.reverse()
          alarm_on = self.this_participant.alarm_on
          type = 'settings'
          message = {
               'participant_list': participant_list,
               'alarm_on': alarm_on
          }
          await self.send_message(type, message)

     async def handle_udpate_chatroom_name(self, message):
          await self.update_chatroom_name(message)
          
          
          
     #----------------EVENT RELATED------------------------------------
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
          print('exit', self.user, user)
          print(self.online_participants)
     
     async def msg(self, event):
          await self.send_message(event['type'], event['message'])
     
     async def exit(self, event):
          await self.send_message('msg', event['message'])
          await self.update_participant_info()
          
     #----------------UTILITY FUNCTIONS---------------------------------
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
          
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
          status_message = {
               'id': self.chatroom_id,
               'name': '',
               'avatar': '',
               'background': '',
               'last_msg': message.get('content'),
               'updated_at': message.get('timestamp'),
          }
          message_info = {
               'type': 'msg', 
               'chat_type': 'private',
               'message': status_message
          }
          
          for user in self.participants:
               print(self.online_participants)
               status_message['update_unread_cnt'] = (user not in self.online_participants)
               await self.channel_layer.group_send(
                    f'status_{user}', 
                    message_info
               )
               
     async def send_user_status_reset_message(self):
          status_message = {
               'id': self.chatroom_id,
               'name': '',
               'avatar': '',
               'background': '',
               'last_msg': '',
               'updated_at': '',
               'update_unread_cnt': None
          }

          await self.channel_layer.group_send(
               f'status_{self.user.pk}',
               {
                    "type": "msg", 
                    "chat_type": "private", 
                    "message": status_message}
          )
          
     #----------------DATABASE RELATED------------------------------------
     @database_sync_to_async
     def udpate_chatroom_name(self, chatroom_name):
          self.this_participant.custom_name = chatroom_name
          self.this_participant.save()
     
     @database_sync_to_async
     def get_participant_list(self):
          participants = self.chatroom.participants.all()
          return UserSimpleDetailSerializer(participants, many=True).data

          
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
          return PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id).count()


     @database_sync_to_async
     def update_offline_participant_unread_cnt(self):
          if not self.other_participant.is_online:
               self.other_participant.unread_cnt += 1
               self.other_participant.save()
     
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
               unread_cnt = 0 if not instance.is_msg else 2 - len(set(self.online_participants))
               return PrivateMessageSerializer(instance, context={'unread_cnt': unread_cnt}).data
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
                    self.this_participant.save()
          except:
               pass
     
     @database_sync_to_async
     def this_participant_was_offline(self):
          return not self.this_participant.is_online
     
     @database_sync_to_async
     def get_chatroom_and_participants_info(self):
          try:
               self.chatroom = PrivateChatRoom.objects.get(id=self.chatroom_id)
               participants = PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id)
               self.participants = list(participants.values_list('user', flat=True))
               self.this_participant = participants.get(user=self.user)
               self.other_participant = participants.exclude(user=self.user).first()
               self.last_read_time = self.this_participant.last_read_time.astimezone(timezone.get_current_timezone())
               self.online_participants = list(participants.filter(is_online=True).values_list('user', flat=True))
               
               return True
          except:
               return False 
          
     @database_sync_to_async
     def get_last_30_messages(self):
          last_read_time_list = PrivateChatParticipant.objects.filter(chatroom=self.chatroom_id, is_online=False).values_list('last_read_time', flat=True)
          messages = self.chatroom.messages.all()[self.loaded_cnt:self.loaded_cnt+30]
          self.loaded_cnt += 30
          return PrivateMessageSerializer(messages, many=True, context={"last_read_time_list": last_read_time_list}).data
   