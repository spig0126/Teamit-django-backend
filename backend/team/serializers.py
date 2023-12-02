from rest_framework import serializers

from .models import *
from position.models import *
from activity.models import *
from user.models import User

# create serializers
class TeamCreateSerializer(serializers.ModelSerializer):
     activity = serializers.CharField(write_only=True, required=False)
     cities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     positions = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)
     user_name = serializers.CharField(write_only=True, required=False)
     
     class Meta: 
          model = Team
          fields = [
               'user_name',
               'name', 
               'short_pr', 
               'activity', 
               'cities', 
               'meet_preference',
               'long_pr', 
               'active_startdate', 
               'active_enddate', 
               'positions', 
               'recruit_startdate', 
               'recruit_enddate'
          ]
          
     def create(self, validated_data):
          activity = validated_data.pop('activity', None)
          cities = validated_data.pop('cities', None)
          positions = validated_data.pop('positions', None)
          user_name = validated_data.pop('user_name', None)
          
          validated_data['activity'] = Activity.objects.get(name=activity)
          
          team_instance = Team.objects.create(**validated_data)
          user_instance = User.objects.get(name=user_name)
          city_instances = []
          try:
               for city in cities:
                    province_name, city_name = city.strip().split()
                    province = Province.objects.get(name=province_name).id
                    city_instances.append(City.objects.get(name=city_name, province=province))
               for position in positions:
                    position_instance = Position.objects.get(name=position['name'])
                    TeamPositions.objects.create(team=team_instance, position=position_instance, cnt=position['cnt'], pr=position['pr'])
               team_instance.cities.set(city_instances)
               TeamMembers.objects.create(team=team_instance, user=user_instance)
          except Province.DoesNotExist:
               team_instance.delete()
               raise serializers.ValidationError({"province": "province does not exist"})
          except (City.DoesNotExist, ValueError):
               team_instance.delete()
               raise serializers.ValidationError({"city": "city does not exist"}) 
          except Position.DoesNotExist:
               team_instance.delete()
               raise serializers.ValidationError({"positions": "certain position does not exist"})
          
          return team_instance

# detail serializers
class TeamPositionDetailSerializer(serializers.ModelSerializer):
     position = serializers.StringRelatedField(read_only=True)
     
     class Meta:
          model = TeamPositions
          fields = [
               'position',
               'pr',
               'cnt', 
          ]

class TeamMemberDetailSerializer(serializers.ModelSerializer):
     user = serializers.StringRelatedField(read_only=True)
     position = serializers.StringRelatedField(read_only=True)
     class Meta:
          model = TeamMembers
          fields = [
               'user',
               'position', 
               'background',
               'avatar'
          ]
          
class TeamDetailSerializer(serializers.ModelSerializer):
     positions = TeamPositionDetailSerializer(many=True, source='teampositions_set')
     members = TeamMemberDetailSerializer(many=True, source='teammembers_set')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'short_pr', 
               'meet_preference',
               'long_pr',
               'active_startdate',
               'active_enddate',
               'recruit_startdate',
               'recruit_enddate',
               'cities',
               'activity',
               'positions',
               'members'
          ]