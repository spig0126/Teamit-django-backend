from rest_framework import serializers
from django.db import transaction

from .models import *
from user.serializers import UserSimpleDetailSerializer
from user.models import User
from team.serializers import TeamSenderDetailSerializer, TeamMemberDetailSerializer
from team.models import TeamMembers


class PrivateChatRoomCreateSerializer(serializers.ModelSerializer):
     participants = serializers.SlugRelatedField(slug_field='name', many=True, queryset=User.objects.all())
     
     class Meta:
          model = PrivateChatRoom
          fields = '__all__'

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
          return PrivateChatRoomDeatilSerializer(instance, context=self.context).data

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

#######################################################
class InquiryChatRoomCreateSerializer(serializers.ModelSerializer):
     inquirer = serializers.SlugRelatedField(slug_field='name', queryset=User.objects.all())
     team = serializers.SlugRelatedField(slug_field='id', queryset=Team.objects.all())
     
     class Meta:
          model = InquiryChatRoom
          fields = '__all__'
     
     def to_representation(self, instance):
          return InquiryChatRoomDetailSerializer(instance).data
          
class InquiryChatRoomDetailSerializer(serializers.ModelSerializer):
     inquirer = UserSimpleDetailSerializer()
     team = TeamSenderDetailSerializer()
     
     class Meta:
          model = InquiryChatRoom
          fields = [
               'id',
               'last_msg',
               'updated_at',
               'inquirer',
               'team'
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

class TeamChatRoomDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamChatRoom
          fields = [
               'id',
               'name',
               'background',
               'last_msg',
               'updated_at'
          ]

