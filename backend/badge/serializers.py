from rest_framework import serializers

from .models import *

class BadeDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = Badge
          fields = [
               'user',
               'attendatnce_level', 
               'friendship_level',
               'team_participance_level',
               'team_post_level',
               'liked_level',
               'recruit_level',
               'team_refusal_status',
               'user_profile_status',
               'team_leader_status',
               'shared_profile_level'
          ]