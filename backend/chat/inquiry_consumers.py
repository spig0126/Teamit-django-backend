import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import *
from .serializers import*
from team.serializers import TeamBasicDetailForChatSerializer
from user.serializers import UserSimpleDetailSerializer
from fcm_notification.tasks import send_fcm_to_user_task

class InquiryChatConsumer(AsyncWebsocketConsumer):
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
          
          was_offline = await self.user_was_offline()
          if was_offline:
               await self.update_user_online()
          
          await self.update_online_participants()
          await self.join_chatroom()
     
     async def disconnect(self, close_code):
          await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
          if self.is_inquirer or self.is_responder:
               await self.send_user_status_reset_message()
               await self.mark_as_offline()
          await self.close()
     
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
     
     #---------------Handle related-------------------
     async def handle_message(self, message):
          msg_details = {
               'chatroom': self.chatroom_id,
               'sender': 'T' if self.is_responder else 'I',
               'content': message['content'],
               'user': self.user.pk if not self.is_responder else None,
               'team': self.team_pk if self.is_responder else None
          }
          message = await self.create_message(msg_details)
          await self.update_chatroom_last_msg(message['content'])
          await self.send_group_message('msg', message)
          await self.send_status_message(message)
          await self.send_offline_participants_fcm(message)
          await self.update_unread_cnt()
     
     async def handle_exit(self):
          chatroom_active = await self.remove_user_from_chatroom()
          if not chatroom_active:
               await self.delete_chatroom()
          else:
               await self.channel_layer.group_discard(self.chatroom_name, self.channel_name)
               name = self.chatroom.team.name if self.is_responder else self.chatroom.inquirer.name
               announcement = {
                    'chatroom': self.chatroom_id,
                    'content': f'{name} 님이 퇴장했습니다',
                    'is_msg': False
               }
               message = await self.create_message(announcement)
               await self.send_group_message('exit', message)
          await self.close()
     
     async def handle_settings(self):
          responder_details = TeamBasicDetailForChatSerializer(self.chatroom.team).data
          inquirer_details = UserSimpleDetailSerializer(self.inquirer).data
          participant_list = [responder_details, inquirer_details] if self.is_responder else [inquirer_details, responder_details]
          alarm_on = self.chatroom.responder_alarm_on if self.is_responder else self.chatroom.inquirer_alarm_on
          type = 'settings'
          message = {
               'participant_list': participant_list,
               'alarm_on': alarm_on
          }
          await self.send_message(type, message)
          
     #---------------event related----------------------
     async def online(self, event):
          user = event['message'].get('user', None)
          print('online', self.user, user)
          print('before', self.online_participants)
          self.online_participants.append(user)
          print('after', self.online_participants)
          
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
     
     async def enter(self, event):
          await self.send_message('msg', event['message'])
          await self.update_participant_info()
          
     #----------------utility related-------------------
     async def send_status_message(self, message):
          # to user's chat status
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
               'chat_type': 'inquiry',
               'filter': 'responder' if self.is_responder else 'inquirer',
               'message': status_message
          }
          
          for user in [self.inquirer, self.responder]:
               status_message['update_unread_cnt'] = (user.pk not in self.online_participants)
               channel_name = f'status_{user.pk}'
               await self.channel_layer.group_send(
                    channel_name, message_info
               )
          
          # to team inquiry status
          status_message = {
               'id': self.chatroom_id,
               'name': '',
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
                    "chat_type": "inquiry", 
                    'filter': 'responder' if self.is_responder else 'inquirer',
                    "message": status_message}
          )
               
     async def send_message(self, type, message):
          await self.send(text_data=json.dumps({
               'type': type,
               'message': message
          }))
          
     async def send_last_30_messages(self):
          message = await self.get_last_30_messages()
          await self.send_message('history', message)
          
     async def join_chatroom(self):
          await self.channel_layer.group_add(self.chatroom_name, self.channel_name)
          await self.accept()
          await self.send_user_roles()
          await self.send_last_30_messages()
          
     
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
               await self.send_group_message('online', {'user': self.user.pk})
          
     
     #----------------DB related------------------------
     @database_sync_to_async
     def send_offline_participants_fcm(self, message):
          title = self.team_name if self.is_inquirer else f'{self.team_name} > {self.inquirer.name}'
          body = message['content']
          data = {
               'page': 'chat',
               'chatroom_name': title,
               'chatroom_id': str(self.chatroom_id),
               'chat_type': 'inquiry'
          }
          if self.is_responder and not self.chatroom.inquirer_is_online:
               send_fcm_to_user_task.delay(self.inquirer.pk, title, body, data)
          elif self.is_inquirer and not self.chatroom.responder_is_online:
               send_fcm_to_user_task.delay(self.responder.pk, title, body, data)
     
     @database_sync_to_async
     def update_alarm_status(self):
          if self.is_responder:
               self.chatroom.responder_alarm_on = not self.chatroom.responder_alarm_on
          else:
               self.chatroom.inquirer_alarm_on = not self.chatroom.inquirer_alarm_on
          self.chatroom.save()
          
     @database_sync_to_async
     def delete_chatroom(self):
          self.chatroom = None
          InquiryChatRoom.objects.get(pk=self.chatroom_id).delete()
          
     @database_sync_to_async
     def remove_user_from_chatroom(self):
          if self.is_responder:
               self.chatroom.team = None
          else:
               self.chatroom.inquirer = None
          self.chatroom.save()
          if self.chatroom.team is None and self.chatroom.inquirer is None:
               return False
          return True
               
     @database_sync_to_async
     def update_unread_cnt(self):
          if self.is_responder:
               if not self.chatroom.inquirer_is_online:
                    self.chatroom.inquirer_unread_cnt += 1
          else:
               if not self.chatroom.responder_is_online:
                    self.chatroom.responder_unread_cnt += 1
          self.chatroom.save()
          
     @database_sync_to_async
     def get_alarm_status(self):
          if self.is_responder:
               return self.chatroom.responder_alarm_on
          return self.chatroom.inquirer_alarm_on
     
     @database_sync_to_async
     def get_chatroom_name(self, user_pk):
          team_name = self.chatroom.team.name
          inquirer_name = self.chatroom.inquirer.name
          
          if user_pk == self.responder.pk:
               return f'{team_name} > {inquirer_name}'
          return team_name
     
     @database_sync_to_async
     @transaction.atomic
     def update_chatroom_last_msg(self, content):
          self.chatroom.last_msg = content
          self.chatroom.save()
          
     @database_sync_to_async
     @transaction.atomic
     def create_message(self, data):
          try:
               serializer = InquiryMessageCreateSeriazlier(data=data)
               serializer.is_valid(raise_exception=True)
               instance = serializer.save()
               return InquiryMessageSerializer(instance).data
          except ValidationError as e:
               self.send_message('error', e.detail)
               
               
     @database_sync_to_async
     def get_last_30_messages(self):
          messages = self.chatroom.messages.all()[self.loaded_cnt:self.loaded_cnt+30]
          self.loaded_cnt += 30
          return InquiryMessageSerializer(messages, many=True).data
     

     @database_sync_to_async
     def update_user_online(self):
          if self.is_responder:
               self.chatroom.responder_is_online = True
               self.chatroom.responder_unread_cnt = 0
          elif self.is_inquirer:
               self.chatroom.inquirer_is_online = True
               self.chatroom.inquirer_unread_cnt = 0
          self.chatroom.save()
     
     @database_sync_to_async
     def update_user_offline(self):
          try:
               self.online_participants.remove(self.user.pk)
          except ValueError:
               pass
          try:
               if self.user not in self.online_participants:
                    if self.is_responder:
                         self.chatroom.responder_is_online = False
                         self.chatroom.responder_unread_cnt = 0
                    elif self.is_inquirer:
                         self.chatroom.inquirer_is_online = False
                         self.chatroom.inquirer_unread_cnt = 0
                    self.chatroom.save()
          except:
               pass
     
     @database_sync_to_async
     def get_chatroom_and_participants_info(self):
          self.chatroom = InquiryChatRoom.objects.get(pk=self.chatroom_id)
          self.team_pk = self.chatroom.team.pk
          self.team_name = self.chatroom.team.name
          
          self.inquirer = self.chatroom.inquirer
          self.responder = self.chatroom.team.responder
          self.is_responder, self.is_inquirer, self.is_member = False, False, False
          if self.responder == self.user:
               self.is_responder = True
          if self.inquirer == self.user:
               self.is_inquirer = True
          self.is_member = self.chatroom.team.members.filter(pk=self.user.pk).exists()
          
          self.online_participants = []
          if self.is_responder or self.is_inquirer:
               if self.chatroom.inquirer_is_online:
                    self.online_participants.append(self.inquirer.pk)
               elif self.chatroom.responder_is_online:
                    self.online_participants.append(self.responder.pk)
          return self.is_inquirer, self.is_responder, self.is_member
     
     @database_sync_to_async
     def user_was_offline(self):
          if self.is_responder:
               return not self.chatroom.responder_is_online
          elif self.is_inquirer:
               return not self.chatroom.inquirer_is_online
          return None

