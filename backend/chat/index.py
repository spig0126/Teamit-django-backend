from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from .models import PrivateChatParticipant, TeamChatParticipant, InquiryChatRoom, InquiryChatParticipant


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
        'searchableAttributes': ['name', 'other_user_name'],
        'attributesToRetrieve': ['id', 'name', 'avatar', 'background', 'last_msg', 'unread_cnt', 'updated_at',
                                 'alarm_on'],
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
        'searchableAttributes': ['name', 'other_participant_names', 'team_name'],
        'attributesToRetrieve': ['id', 'name', 'avatar', 'background', 'last_msg', 'unread_cnt', 'updated_at',
                                 'alarm_on'],
    }
    index_name = 'team_chat_participant_index'


@register(InquiryChatParticipant)
class InquiryChatParticipantIndex(AlgoliaIndex):
    fields = (
        ('chatroom_pk', 'id'),
        ('chatroom_name', 'name'),
        'avatar',
        'background',
        'last_msg',
        'unread_cnt',
        'updated_at',
        'alarm_on',
        'is_user',
    )
    settings = {
        'searchableAttributes': ['name'],
        'attributesToRetrieve': ['id', 'name', 'avatar', 'background', 'last_msg', 'unread_cnt', 'updated_at',
                                 'alarm_on'],
    }
    index_name = 'inquiry_chatroom_index'
