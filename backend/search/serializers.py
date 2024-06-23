from rest_framework import serializers

from .models import *
from user.serializers import UserDetailSerializer
from team.serializers import SearchedTeamDetailSerializer


class UserSearchHistoryDetailSerializer(serializers.ModelSerializer):
    search_query = serializers.CharField(allow_blank=True)

    class Meta:
        model = UserSearchHistory
        fields = '__all__'


class TeamSearchHistoryDetailSerializer(serializers.ModelSerializer):
    search_query = serializers.CharField(allow_blank=True)

    class Meta:
        model = TeamSearchHistory
        fields = '__all__'


class SearchedUserHistoryDetailSerializer(serializers.ModelSerializer):
    searched_user = UserDetailSerializer()

    class Meta:
        model = UserSearchHistory
        fields = [
            'id',
            'searched_user'
        ]


class SearchedTeamHistoryDetailSerializer(serializers.ModelSerializer):
    searched_team = SearchedTeamDetailSerializer()

    class Meta:
        model = UserSearchHistory
        fields = [
            'id',
            'searched_team'
        ]
