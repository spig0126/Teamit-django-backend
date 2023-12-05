from rest_framework import serializers, status

from .models import *
from team.models import TeamApplication
from team.serializers import TeamApplicantDetailSerializer

# detail serializers
class TeamNotificationDetailSerializer(serializers.ModelSerializer):
     sender = serializers.SerializerMethodField()
     class Meta:
          model = TeamNotification
          fields = [
               'id', 
               'type',
               'created_at',
               'is_read',
               'sender'
          ]
     
     def get_sender(self, obj):
          team_application = self.instance.related
          applicant = team_application.applicant
          sender_data = TeamApplicantDetailSerializer({'user': applicant, 'team_application': team_application}).data
          return sender_data
          