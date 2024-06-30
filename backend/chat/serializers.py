from rest_framework import serializers
from django.db import transaction

from .models import *
from user.serializers import UserMinimalWithAvatarBackgroundDetailSerializer
from user.models import User
from team.serializers import TeamMemberDetailSerializer
from team.models import TeamMembers
from django.core.files.storage import default_storage
from user.serializers import UserMinimalDetailSerializer


PrivateReadTillHereMessage = {
    'id': -1,
    'content': '',
    'timestamp': '',
    'name': '',
    'avatar': '',
    'background': '',
    'is_msg': False,
}

TeamReadTillHereMessage = {
    'id': -1,
    'content': '',
    'timestamp': '',
    'name': '',
    'avatar': '',
    'position': '',
    'background': '',
    'is_msg': False,
    'user': None
}

InquiryReadTillHereMessage = {
    'id': -1,
    'sender': None,
    'content': '',
    'timestamp': '',
    'name': '',
    'avatar': '',
    'background': '',
    'is_msg': False,
}

class PrivateChatRoomCreateSerializer(serializers.ModelSerializer):
    participants = serializers.SlugRelatedField(slug_field='name', many=True, queryset=User.objects.all())

    class Meta:
        model = PrivateChatRoom
        fields = ['participants']

    @transaction.atomic
    def create(self, validated_data):
        participants = validated_data.pop('participants', [])
        validated_data['user1'] = User.objects.get(name=participants[0])
        validated_data['user2'] = User.objects.get(name=participants[1])
        chatroom = PrivateChatRoom.objects.create(**validated_data)

        creating_user = self.context.get('user')
        other_user = chatroom.user1 if creating_user == chatroom.user2 else chatroom.user2
        PrivateChatParticipant.objects.create(
            chatroom=chatroom,
            user=creating_user
        )
        if creating_user not in other_user.blocked_users.all():
            PrivateChatParticipant.objects.create(
                chatroom=chatroom,
                user=other_user
            )
        return chatroom

    def to_representation(self, instance):
        chatroom_name = PrivateChatParticipant.objects.get(chatroom=instance,
                                                           user=self.context.get('user')).chatroom_name
        return {'chatroom_id': instance.id, "chatroom_name": chatroom_name}


class PrivateChatRoomDetailSerializer(serializers.ModelSerializer):
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
        return UserMinimalWithAvatarBackgroundDetailSerializer(sender).data


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
            serializer = PrivateChatRoomDetailSerializer(instance.chatroom, context=self.context)
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
    class Meta:
        model = PrivateMessage
        fields = [
            'id',
            'content',
            'timestamp',
            'name',
            'avatar',
            'background',
            'is_msg'
        ]


#######################################################
class InquiryChatRoomCreateSerializer(serializers.ModelSerializer):
    inquirer = serializers.SlugRelatedField(slug_field='name', queryset=User.objects.all())
    team = serializers.SlugRelatedField(slug_field='id', queryset=Team.objects.all())

    class Meta:
        model = InquiryChatRoom
        fields = '__all__'

    def to_representation(self, instance):
        return {'chatroom_id': instance.id, 'chatroom_name': instance.inquirer_chatroom_name}


class InquiryChatRoomDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='chatroom.pk', read_only=True)
    name = serializers.CharField(source='chatroom_name')
    updated_at = serializers.CharField(source='chatroom.updated_at')

    class Meta:
        model = InquiryChatParticipant
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


class InquiryChatRoomDetailForTeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='team_chatroom_name')
    avatar = serializers.CharField(source='inquirer_avatar')
    background = serializers.CharField(source='inquirer_background')

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


class InquiryMessageCreateSerializer(serializers.ModelSerializer):
    chatroom = serializers.SlugRelatedField(slug_field='pk', queryset=InquiryChatRoom.objects.all())
    is_msg = serializers.BooleanField(default=True, required=False)
    sender = serializers.CharField(required=False)

    class Meta:
        model = InquiryMessage
        fields = [
            'chatroom',
            'content',
            'sender',
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
            'is_msg',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data['is_msg']:
            for key in ('name', 'avatar', 'background'):
                data[key] = ''
        return data


#######################################################
class TeamChatParticipantDetailSerializer(serializers.ModelSerializer):
    user = UserMinimalWithAvatarBackgroundDetailSerializer()
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
        chatroom_name = TeamChatParticipant.objects.get(chatroom=instance, user=self.context.get('user')).chatroom_name
        return {'chatroom_id': instance.id, "chatroom_name": chatroom_name}


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
        participant = TeamChatParticipant.objects.filter(user=self.context.get('user'), chatroom=instance.id).values(
            'unread_cnt').first()
        return participant['unread_cnt']

    def get_alarm_on(self, instance):
        participant = TeamChatParticipant.objects.filter(user=self.context.get('user'), chatroom=instance.id).values(
            'alarm_on').first()
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
    user = UserMinimalDetailSerializer()

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
            'is_msg',
            'user'
        ]


class TeamChatParticipantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamChatParticipant
        fields = [
            'chatroom',
            'user',
            'member'
        ]
