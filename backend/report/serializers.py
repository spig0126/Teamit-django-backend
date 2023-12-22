from rest_framework import serializers

from .models import *
from user.serializers import UserField

class ReasonField(serializers.Field):
     def to_internal_value(self, data):
          # Convert human-readable report reasons to actual values
          for choice in Report.REASON_CHOICES:
               if data == choice[1]:
                    return data
          raise serializers.ValidationError("Invalid choice")
     
     def to_representation(self, obj):
          return dict(Report.REASON_CHOICES).get(obj, obj)

class ReportDetailSerializer(serializers.ModelSerializer):
     reason = ReasonField()
     reporter = UserField()
     
     class Meta:
          model = Report
          fields = [
               'reporter',
               'reported_type',
               'reported_user',
               'reported_team',
               'reason',
          ]