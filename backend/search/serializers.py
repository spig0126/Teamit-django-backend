from rest_framework import serializers

from .models import *
from user.serializers import UserField

class UserSearchHistoryDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = UserSearchHistory
          fields = '__all__'
   
class TeamSearchHistoryDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamSearchHistory
          fields = '__all__'
   
          