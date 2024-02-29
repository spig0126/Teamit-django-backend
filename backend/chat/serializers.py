from rest_framework import serializers
from django.db import transaction

from .models import *
from user.serializers import UserSimpleDetailSerializer
from user.models import User
from team.serializers import TeamMemberDetailSerializer
from team.models import TeamMembers
from django.core.files.storage import default_storage


class PrivateChatRoomCreateSerializer(serializers.ModelSerializer):
     participants = serializers.SlugRelatedField(slug_field='name', many=True, queryset=User.objects.all())
     
     class Meta:
          model = PrivateChatRoom
          fields = ['participants']

     @transaction.atomic
     def create(self, validated_data):
          participants = validated_data.pop('participants', [])
          chatroom = PrivateChatRoom.objects.create(**validated_data)
          for participant, i in zip(participants, range(1, 3)):
               user = User.objects.get(name=participant)
               PrivateChatParticipant.objects.create(
                    chatroom=chatroom,
                    chatroom_name = participants[-i],
                    user=user
               )
          return chatroom
     
     def to_representation(self, instance):
          return {'chatroom_id': instance.id}

class PrivateChatRoomDeatilSerializer(serializers.ModelSerializer):
     sender = serializers.SerializerMethodField()
     name = serializers.SerializerMethodField()
     
     class Meta:
          model = PrivateChatRoom
          fields = [
               'id',
               'name',
               'last_msg',
               'updated_at',
               'sender'
               ]
     
     def get_name(self, instance):
          participant = PrivateChatParticipant.objects.get(chatroom=instance, user=self.context.get('user'))
          return participant.chatroom_name
     
     def get_sender(self, instance):
          sender = instance.participants.exclude(id=self.context.get('user').id).first()
          return UserSimpleDetailSerializer(sender).data

class MyPrivateChatRoomDetailSerializer(serializers.ModelSerializer):
     id = serializers.PrimaryKeyRelatedField(source='chatroom', read_only=True)
     name = serializers.CharField(source='chatroom_name')
     updated_at = serializers.DateTimeField(source='chatroom.updated_at')
     
     class Meta:
          model = PrivateChatParticipant
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'last_msg',
               'unread_cnt',
               'updated_at',
               'alarm_on'
               ]
          
class PrivateChatRoomNameSerializer(serializers.ModelSerializer):
     class Meta:
          model = PrivateChatParticipant
          fields = [
               'chatroom',
               'chatroom_name'
               ]

class PrivateChatParticipantDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = PrivateChatParticipant
          fields = '__all__'
     
     def to_representation(self, instance):          
          request = self.context['request']
          if request and request.method == 'PATCH':
               serializer = PrivateChatRoomDeatilSerializer(instance.chatroom, context=self.context)
               return serializer.data
          return super().to_representation(instance)

class PrivateMessageCreateSerializer(serializers.ModelSerializer):
     chatroom = serializers.SlugRelatedField(slug_field='pk', queryset=PrivateChatRoom.objects.all())
     sender = serializers.SlugRelatedField(slug_field='pk', required=False, queryset=User.objects.all())
     is_msg = serializers.BooleanField(default=True, required=False)
     
     class Meta:
          model = PrivateMessage
          fields = [
               'chatroom',
               'content',
               'sender',
               'is_msg'
          ]
          
class PrivateMessageSerializer(serializers.ModelSerializer):
     unread_cnt = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
          model = PrivateMessage
          fields = [
               'id',
               'content',
               'timestamp',
               'name',
               'avatar',
               'background',
               'unread_cnt',
               'is_msg'
          ]
          
     def get_unread_cnt(self, instance):
          try:
               return self.context['unread_cnt']
          except KeyError:
               if instance.is_msg:
                    return sum(1 for lut in self.context['last_read_time_list'] if lut < instance.timestamp)
               else:
                    return 0
               
#######################################################
class InquiryChatRoomCreateSerializer(serializers.ModelSerializer):
     inquirer = serializers.SlugRelatedField(slug_field='name', queryset=User.objects.all())
     team = serializers.SlugRelatedField(slug_field='id', queryset=Team.objects.all())
     
     class Meta:
          model = InquiryChatRoom
          fields = '__all__'
     
     def to_representation(self, instance):
          return {'chatroom_id': instance.id}

class InquiryChatRoomDetailSerializer(serializers.ModelSerializer):
     unread_cnt = serializers.SerializerMethodField()
     avatar = serializers.SerializerMethodField()
     background = serializers.SerializerMethodField()
     name = serializers.SerializerMethodField()
     alarm_on = serializers.SerializerMethodField()
     
     class Meta:
          model = InquiryChatRoom
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'last_msg',
               'unread_cnt',
               'updated_at',
               'alarm_on'
          ]
     
     def get_unread_cnt(self, instance):
          if self.context['user'] == instance.inquirer:
               return instance.inquirer_unread_cnt
          else:
               return instance.responder_unread_cnt
          
     def get_avatar(self, instance):
          if self.context['user'] == instance.inquirer:
               return instance.team.image.url or default_storage.url('teams/default.png')
          return instance.inquirer.avatar.url or default_storage.url('avatars/default.png')
     
     def get_background(self, instance):
          if self.context['user'] == instance.inquirer:
               return ''
          return instance.inquirer.background.url or ''
     
     def get_name(self, instance):
          team_name = instance.team.name
          inquirer_name = instance.inquirer.name
          
          if self.context['user'] == instance.inquirer:
               return team_name
          else:
               return f'{team_name} > {inquirer_name}'
     
     def get_alarm_on(self, instance):
          if self.context['user'] == instance.inquirer:
               return instance.inquirer_alarm_on
          else:
               return instance.responder_alarm_on
          
class InquiryChatRoomWithTypeDetailSerializer(serializers.ModelSerializer):
     type = serializers.SerializerMethodField()
     unread_cnt = serializers.SerializerMethodField()
     avatar = serializers.SerializerMethodField()
     background = serializers.SerializerMethodField()
     name = serializers.SerializerMethodField()
     alarm_on = serializers.SerializerMethodField()
     
     class Meta:
          model = InquiryChatRoom
          fields = [
               'id',
               'type',
               'name',
               'avatar',
               'background',
               'last_msg',
               'unread_cnt',
               'updated_at',
               'alarm_on'
          ]
          
     def get_type(self, instance):
          return self.context['type']
     
     def get_unread_cnt(self, instance):
          if self.context['type'] == 'inquirer':
               return instance.inquirer_unread_cnt
          else:
               return instance.responder_unread_cnt
          
     def get_avatar(self, instance):
          if self.context['type'] == 'inquirer':
               return instance.team.image.url or default_storage.url('teams/default.png')
          else:
               return instance.inquirer.avatar.url or default_storage.url('avatars/default.png')
     
     def get_background(self, instance):
          if self.context['type'] == 'inquirer':
               return ''
          else:
               return instance.inquirer.background.url or ''
     
     def get_name(self, instance):
          team_name = instance.team.name
          inquirer_name = instance.inquirer.name
          
          if self.context['type'] == 'inquirer':
               return team_name
          else:
               return f'{team_name} > {inquirer_name}'
     
     def get_alarm_on(self, instance):
          if self.context['type'] == 'inquirer':
               return instance.inquirer_alarm_on
          else:
               return instance.responder_alarm_on
          
class InquiryChatRoomDetailForTeamSerializer(serializers.ModelSerializer):
     avatar = serializers.SerializerMethodField()
     background = serializers.SerializerMethodField()
     name = serializers.SerializerMethodField()
     
     class Meta:
          model = InquiryChatRoom
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'last_msg',
               'updated_at',
          ]
     
     def get_name(self, instance):
          if instance.inquirer is None:
               return '(알 수 없음)'
          return instance.inquirer.name
     
     def get_avatar(self, instance):
          if instance.inquirer is None:
               return ''
          return instance.inquirer.avatar.url
     
     def get_background(self, instance):
          if instance.inquirer is None:
               return ''
          return instance.inquirer.background.url
     
class InquiryMessageCreateSeriazlier(serializers.ModelSerializer):
     chatroom = serializers.SlugRelatedField(slug_field='pk', queryset=InquiryChatRoom.objects.all())
     is_msg = serializers.BooleanField(default=True, required=False)
     sender = serializers.CharField(required=False)
     user = serializers.SlugRelatedField(slug_field='pk', required=False, allow_null=True, queryset=User.objects.all())
     team = serializers.SlugRelatedField(slug_field='pk', required=False, allow_null=True, queryset=Team.objects.all())
     
     class Meta:
          model = InquiryMessage
          fields = [
               'chatroom',
               'content',
               'sender',
               'user',
               'team',
               'is_msg'
          ]
          
class InquiryMessageSerializer(serializers.ModelSerializer):
     class Meta:
          model = InquiryMessage
          fields = [
               'id',
               'sender',
               'content',
               'timestamp',
               'name',
               'avatar',
               'background',
               'is_msg'
          ]
          
#######################################################
class TeamChatParticipantDetailSerializer(serializers.ModelSerializer):
     user = UserSimpleDetailSerializer()
     member = TeamMemberDetailSerializer()
     
     class Meta:
          model = TeamChatParticipant
          fields = [
               'user', 
               'member'
          ]

class TeamChatRoomCreateSerializer(serializers.ModelSerializer):
     participants = serializers.SlugRelatedField(slug_field='pk', many=True, queryset=TeamMembers.objects.all())
     last_msg = serializers.CharField(read_only=True)
     
     class Meta:
          model = TeamChatRoom
          fields = '__all__'
          
     def validate_participants(self, value):
          team_members = TeamMembers.objects.filter(team=self.context.get('team_pk'))
          for participant in value:
               if participant not in team_members:
                    raise serializers.ValidationError(
                         f"Some are not members of this team"
                    )
          return value
     
     def create(self, validated_data):
          participants = validated_data.pop('participants', [])
          team_chat_room = super().create(validated_data)

          for member in participants:
               TeamChatParticipant.objects.create(
                    chatroom=team_chat_room,
                    user=member.user,
                    member=member 
               )

          return team_chat_room

     def to_representation(self, instance):
          return {'chatroom_id': instance.id}

class TeamChatRoomDetailSerializer(serializers.ModelSerializer):
     avatar = serializers.SerializerMethodField()
     unread_cnt = serializers.SerializerMethodField()
     alarm_on = serializers.SerializerMethodField()
     
     class Meta:
          model = TeamChatRoom
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'unread_cnt',
               'last_msg',
               'updated_at',
               'alarm_on'
          ]
     
     def get_avatar(self, instance):
          return ''
     
     def get_unread_cnt(self, instance):
          participant = TeamChatParticipant.objects.filter(user=self.context.get('user'), chatroom=instance.id).values('unread_cnt').first()
          return participant['unread_cnt']

     def get_alarm_on(self, instance):
          participant = TeamChatParticipant.objects.filter(user=self.context.get('user'),chatroom=instance.id).values('alarm_on').first()
          return participant['alarm_on']

class TeamChatRoomUpdateSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamChatRoom
          fields = ['name', 'background']
          
class TeamMessageCreateSerialzier(serializers.ModelSerializer):
     chatroom = serializers.SlugRelatedField(slug_field='pk', queryset=TeamChatRoom.objects.all())
     user = serializers.SlugRelatedField(slug_field='pk', required=False, queryset=User.objects.all())
     member = serializers.SlugRelatedField(slug_field='pk', required=False, queryset=TeamMembers.objects.all())
     is_msg = serializers.BooleanField(default=True, required=False)
     
     class Meta:
          model = TeamMessage
          fields = [
               'chatroom',
               'user',
               'member',
               'content',
               'is_msg'
          ]

class TeamMessageSerializer(serializers.ModelSerializer):
     unread_cnt = serializers.SerializerMethodField(read_only=True)
     
     class Meta:
          model = TeamMessage
          fields = [
               'id',
               'content',
               'timestamp',
               'name',
               'avatar',
               'position',
               'background',
               'unread_cnt',
               'is_msg'
          ]
          
     def get_unread_cnt(self, instance):
          try:
               return self.context['unread_cnt']
          except KeyError:
               if instance.is_msg:
                    return sum(1 for lut in self.context['last_read_time_list'] if lut < instance.timestamp)
               else:
                    return 0
     
class TeamChatParticipantCreateSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamChatParticipant
          fields = [
               'chatroom',
               'user',
               'member'
          ]

     # def to_representation(self, instance):
     #      return {'id': instance.pk}