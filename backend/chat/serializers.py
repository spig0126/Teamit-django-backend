from rest_framework import serializers
from django.db import transaction

from .models import *
from user.serializers import UserSimpleDetailSerializer
from user.models import User


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
               'created_at',
               'updated_at',
               'sender'
               ]
     
     def get_name(self, instance):
          participant = PrivateChatParticipant.objects.get(chatroom=instance, user=self.context.get('user'))
          return participant.chatroom_name
     
     def get_sender(self, instance):
          sender = instance.participants.exclude(id=self.context.get('user').id).first()
          return UserSimpleDetailSerializer(sender).data

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