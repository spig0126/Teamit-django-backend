from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from .models import PrivateChatParticipant, TeamChatParticipant, InquiryChatRoom

@register(PrivateChatParticipant)
class PrivateChatParticipantIndex(AlgoliaIndex):
     fields = (
          ('chatroom_pk', 'id'), 
          ('chatroom_name', 'name'), 
          'avatar',
          'background',
          'last_msg',
          'unread_cnt',
          'updated_at',
          'alarm_on',
          'other_user_name',
          'other_user_pk',
          'user_pk',
     )
     settings = {
          'searchableAttributes': ['chatroom_name', 'other_user_name'],
          'attributesToRetrieve': ['id', 'name', 'avatar', 'background', 'last_msg', 'unread_cnt', 'updated_at', 'alarm_on'],
     }
     index_name = 'private_chat_participant_index'

@register(TeamChatParticipant)
class TeamChatParticipantIndex(AlgoliaIndex):
     fields = (
          ('chatroom_pk', 'id'), 
          ('chatroom_name', 'name'), 
          ('chatroom_avatar', 'avatar'),
          ('chatroom_background', 'background'),
          ('chatroom_last_msg', 'last_msg'),
          'unread_cnt',
          ('chatroom_updated_at', 'updated_at'),
          'alarm_on',
          'other_participant_names',
          'user_pk',
          'team_name'
     )
     settings = {
          'searchableAttributes': ['chatroom_name', 'other_participant_names', 'team_name'],
          'attributesToRetrieve': ['id', 'name', 'avatar', 'background', 'last_msg', 'unread_cnt', 'updated_at', 'alarm_on'],
     }
     index_name = 'team_chat_participant_index'

@register(InquiryChatRoom)
class InquiryChatRoomIndex(AlgoliaIndex):
     fields = (
          'inquirer_name',
          'team_name',
          'inquirer_pk', 
          'responder_pk'
     )
     settings = {
          'searchableAttributes': ['inquirer_name', 'team_name']
     }
     index_name = 'inquiry_chatroom_index'
