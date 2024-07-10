from rest_framework import serializers
from django.core.files.storage import default_storage
from django.db import transaction

from .models import *
from user.serializers import UserMinimalWithAvatarDetailSerializer, UserUpdateSerializer
from badge.serializers import BadgeImageField


class ProfileCardDetailSerializer(serializers.ModelSerializer):
    user = UserMinimalWithAvatarDetailSerializer()
    interest = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = ProfileCard
        fields = '__all__'

    def get_interest(self, instance):
        return str(instance.user.interests.get(userinterest__priority=instance.interest))

    def get_position(self, instance):
        return str(instance.user.positions.get(userposition__priority=instance.position))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['badge_one'] = data['badge_one'] or ''
        data['badge_two'] = data['badge_two'] or ''
        return data


class ProfileCardUpdateInfoSerializer(serializers.Serializer):
    current_profile_card = ProfileCardDetailSerializer(source='*', read_only=True)
    tab_info = serializers.SerializerMethodField()

    def get_tab_info(self, instance):
        card = instance
        user = card.user
        current_badges = set([card.badge_one.url, card.badge_two.url])
        
        data = {}
        data['interests'] = list(str(interest) for interest in user.interests.all())
        data['positions'] = list(str(position) for position in user.positions.all())
        files = default_storage.listdir('avatars/')[1]
        data['avatars'] = {i: default_storage.url(f'avatars/{i}.png') for i in range(1, len(files))}
        data['badges'] = sorted(list(set(user.badge.latest_badge_images).union(current_badges))) 

        return data


class ProfileCardUpdateSerializer(serializers.ModelSerializer):
    user = UserUpdateSerializer()
    badge_one = BadgeImageField()
    badge_two = BadgeImageField()
    interest_idx = serializers.IntegerField(source='interest')
    position_idx = serializers.IntegerField(source='position')

    class Meta:
        model = ProfileCard
        fields = [
            'user',
            'bg_idx',
            'badge_bg_idx',
            'interest_idx',
            'position_idx',
            'badge_one',
            'badge_two'
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = self.fields['user']

            user_serializer.update(instance.user, user_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ProfileCardDetailSerializer(instance, context={'user': instance.user}).data
