from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import *
from position.models import *
from activity.models import *
from user.models import User

# create serializers
class TeamCreateUpdateSerializer(serializers.ModelSerializer):
     activity = serializers.CharField(write_only=True, required=False)
     cities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     positions = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)
     creator = serializers.CharField(write_only=True)
     creator_background = serializers.CharField(write_only=True)
     
     class Meta: 
          model = Team
          fields = [
               'name', 
               'creator',
               'creator_background',
               'short_pr', 
               'activity', 
               'cities', 
               'meet_preference',
               'long_pr', 
               'active_startdate', 
               'active_enddate', 
               'keywords',
               'positions', 
               'recruit_startdate', 
               'recruit_enddate'
          ]
          
     def create(self, validated_data):
          activity = validated_data.pop('activity', None)
          cities = validated_data.pop('cities', None)
          positions = validated_data.pop('positions', None)
          creator = validated_data.pop('creator', None)
          creator_background = validated_data.pop('creator_background', None)
          
          validated_data['activity'] = Activity.objects.get(name=activity)
          validated_data['creator'] = User.objects.get(name=creator)
          
          team_instance = Team.objects.create(**validated_data)
          user_instance = User.objects.get(name=creator)
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
               TeamMembers.objects.create(team=team_instance, user=user_instance, background=creator_background)
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
     
     def update(self, instance, validated_data):
          for attr, value in validated_data.items():
               if attr == 'activity':
                    new_activity = get_object_or_404(Activity, name=value)
                    instance.activity = new_activity
               elif attr == 'cities':
                    city_instances = []
                    for city in value:
                         province_name, city_name = city.strip().split()
                         province = Province.objects.get(name=province_name).id
                         city_instances.append(get_object_or_404(City, name=city_name, province=province))
                    instance.cities.set(city_instances)
               elif attr == 'positions':
                    for position_data in value:
                         position = get_object_or_404(Position, name=position_data["name"])
                         if TeamPositions.objects.filter(team=instance, position=position).exists():
                              team_position = get_object_or_404(TeamPositions, team=instance, position=position)
                              team_position.cnt = position_data["cnt"]
                              team_position.save()
                         else:
                              TeamPositions.objects.create(team=instance, position=position, cnt=position_data['cnt'], pr=position_data['pr'])
               else:
                    setattr(instance, attr, value)
          instance.save()
          return instance
                    

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
          fields = '__all__'
          
class TeamDetailSerializer(serializers.ModelSerializer):
     positions = TeamPositionDetailSerializer(many=True, source='teampositions_set')
     members = TeamMemberDetailSerializer(many=True, source='teammembers_set')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     creator = serializers.StringRelatedField()
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'creator',
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

class TeamSenderDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'image'
          ]
     
class TeamApplicationSimpleDetailSerializer(serializers.ModelSerializer):
     position = serializers.StringRelatedField()
     class Meta:
          model = TeamApplication
          fields = [
               'id',
               'position',
               'accepted'
          ]
          
class TeamNotificationSenderDetailSerializer(serializers.Serializer):
     id = serializers.IntegerField()
     name = serializers.CharField()
     avatar = serializers.CharField()
     background = serializers.CharField()
     position = serializers.CharField()
     accepted = serializers.BooleanField()
     
     def to_representation(self, instance):
          data = {}
          if 'user' in instance:
               user = instance['user']
               data['id'] = user.pk
               data['name'] = user.name
               data['avatar']= user.avatar
               data['background'] = user.background
          if 'team_application' in instance:
               team_application = instance['team_application']
               data['position'] = team_application.position.name
               data['accepted'] = team_application.accepted
          return data
     
# class MyTeamDetailSerializer(serializers.ModelSerializer):

class TeamSimpleDetailSerializer(serializers.ModelSerializer):   # need to add notification
     positions = serializers.StringRelatedField(many=True)
     member_cnt = serializers.SerializerMethodField()
     activity = serializers.StringRelatedField()
     date_status = serializers.SerializerMethodField()
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'activity',
               'keywords', 
               'date_status',
               'member_cnt',
               'positions'
          ]
          
     def get_member_cnt(self, obj):
          return obj.member_cnt
     def get_date_status(self, obj):
          return obj.date_status
     
class TeamApplicationDetailSerializer(serializers.ModelSerializer):
     team = serializers.StringRelatedField()
     applicant = serializers.StringRelatedField()
     position = serializers.StringRelatedField()
     class Meta:
          model = TeamApplication
          fields = '__all__'