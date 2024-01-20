from rest_framework import serializers, status
from re import match

from .models import *
from team.models import TeamApplication
from team.serializers import TeamSenderDetailSerializer, TeamApplicationSimpleDetailSerializer
from user.serializers import UserSimpleDetailSerializer
from user.models import FriendRequest

class TeamNotificationDetailSerializer(serializers.ModelSerializer):
     team_application = TeamApplicationSimpleDetailSerializer(source='related')
     sender = UserSimpleDetailSerializer(source='related.applicant')
     
     class Meta:
          model = TeamNotification
          fields = [
               'id', 
               'type',
               'created_at',
               'sender',
               'team_application'
          ]
     
class NotificationDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = Notification
          fields = [
               'id', 
               'type',
               'created_at'
          ]
          
     def to_representation(self, instance):
          data = super().to_representation(instance)

          if match('f', data['type']):  # if related to friends
               try:
                    friend_request = FriendRequest.objects.get(pk=instance.related_id)
                    sender = None
                    if data['type'] == 'friend_request_accepted':
                         sender = friend_request.to_user
                    else:
                         sender = friend_request.from_user
                    data['sender'] = UserSimpleDetailSerializer(sender).data
                    data['accepted'] = friend_request.accepted
               except FriendRequest.DoesNotExist:
                    data['sender'] = None
          else:      # if related to team 
               try:
                    team_application = TeamApplication.objects.get(pk=instance.related_id)
                    sender_team = team_application.team
                    data['sender_team'] = TeamSenderDetailSerializer(sender_team).data
                    data['team_application'] = TeamApplicationSimpleDetailSerializer(team_application).data
               except TeamApplication.DoesNotExist:
                    data['sender_team'] = None
          return data