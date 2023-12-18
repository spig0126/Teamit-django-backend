from django.shortcuts import get_object_or_404
from rest_framework import serializers
from datetime import *

from .models import *
from position.models import *
from activity.models import *
from .utils import get_team_members_with_creator_first
from user.models import User

# create serializers
class TeamCreateUpdateSerializer(serializers.ModelSerializer):
     activity = serializers.CharField(write_only=True, required=False)
     interest = serializers.CharField(write_only=True, required=False)
     cities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     positions = serializers.ListField(child=serializers.JSONField(), write_only=True, required=False)
     creator_background = serializers.CharField(write_only=True)
     creator_position = serializers.CharField(write_only=True)
     
     class Meta: 
          model = Team
          fields = [
               'name', 
               'creator',
               'creator_background',
               'creator_position',
               'short_pr', 
               'keywords',
               'activity', 
               'interest',
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
          request = self.context.get('request')

          activity = validated_data.pop('activity', None)
          interest = validated_data.pop('interest', None)
          cities = validated_data.pop('cities', None)
          positions = validated_data.pop('positions', None)
          creator_background = validated_data.pop('creator_background', None)
          creator_position = validated_data.pop('creator_position', None)
          
          validated_data['activity'] = Activity.objects.get(name=activity)
          validated_data['interest'] = Interest.objects.get(name=interest)
          validated_data['creator'] = User.objects.get(pk=int(request.headers.get('UserID')))
          
          team_instance = Team.objects.create(**validated_data)
          user_instance = validated_data['creator']
          city_instances = []
          creator_position = Position.objects.get(name=creator_position)
          try:
               for city in cities:
                    province_name, city_name = city.strip().split(' ', 1)
                    province = Province.objects.get(name=province_name).id
                    city_instances.append(City.objects.get(name=city_name, province=province))
               for position in positions:
                    position_instance = Position.objects.get(name=position['name'])
                    TeamPositions.objects.create(team=team_instance, position=position_instance, cnt=position['cnt'], pr=position['pr'])
               team_instance.cities.set(city_instances)
               TeamMembers.objects.create(team=team_instance, user=user_instance, background=creator_background, position=creator_position)
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
               elif attr == 'interest':
                    new_interest = get_object_or_404(Interest, name=value)
                    instance.interest = new_interest
               elif attr == 'cities':
                    city_instances = []
                    for city in value:
                         province_name, city_name = city.strip().split(' ', 1)
                         province = Province.objects.get(name=province_name).id
                         city_instances.append(get_object_or_404(City, name=city_name, province=province))
                    instance.cities.set(city_instances)
               elif attr == 'positions':
                    for position_data in value:
                         position = get_object_or_404(Position, name=position_data['position'])
                         TeamPositions.objects.create(team=instance, position=position, cnt=position_data['cnt'], pr=position_data['pr'])
               else:
                    setattr(instance, attr, value)
          instance.save()
          return instance
     
     def to_representation(self, instance):
          return MyTeamDetailSerializer(instance).data

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

class MyTeamDetailSerializer(serializers.ModelSerializer):
     positions = TeamPositionDetailSerializer(many=True, source='teampositions_set')
     members = TeamMemberDetailSerializer(many=True, source='teammembers_set')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     creator = serializers.StringRelatedField()
     
     class Meta:
          model = Team
          fields = [
               'id',
               'name', 
               'creator',
               'short_pr', 
               'keywords',
               'activity', 
               'interest',
               'cities', 
               'meet_preference',
               'long_pr', 
               'active_startdate', 
               'active_enddate', 
               'positions', 
               'recruit_startdate', 
               'recruit_enddate',
               'members'
          ]  

class MyTeamRoomDetailSerializer(serializers.ModelSerializer):
     members = TeamMemberDetailSerializer(many=True, source='teammembers_set')
     last_post = serializers.SerializerMethodField()
     has_new_team_notifications = serializers.SerializerMethodField()
     
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'creator',
               'has_new_team_notifications',
               'members',
               'last_post'
          ]  
     
     def get_last_post(self, instance):
          team_posts = instance.posts.all()
          if team_posts:
               return team_posts.order_by('created_at').first().content
          else:
               return None
     
     def get_has_new_team_notifications(self, instance):
          return get_object_or_404(TeamMembers, team=instance, user=self.context.get('user')).noti_unread_cnt > 0
     
     def to_representaation(self, instance):
          data = super().to_representaation(instance)
          members = get_team_members_with_creator_first(instance)
          data['members'] = members
          return data
          
class TeamDetailSerializer(serializers.ModelSerializer):
     positions = TeamPositionDetailSerializer(many=True, source='teampositions_set')
     members = TeamMemberDetailSerializer(many=True, source='teammembers_set')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     is_member = serializers.SerializerMethodField()
     likes = serializers.SerializerMethodField()
     date_status = serializers.SerializerMethodField()
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'creator',
               'date_status',
               'likes',
               'is_member',
               'short_pr',
               'keywords', 
               'activity',
               'interest',
               'cities',
               'meet_preference',
               'active_startdate',
               'active_enddate',
               'long_pr',
               'recruit_startdate',
               'recruit_enddate',
               'positions',
               'members'
          ]  
          
     def get_is_member(self, instance):
          request = self.context.get('request')
          user = get_object_or_404(User, pk=request.headers.get('UserID'))
          if user in instance.members.all():
               return True
          elif TeamApplication.objects.filter(applicant=user, team=instance, accepted=None).exists():
               return None
          return False
     def get_likes(self, instance):
          request = self.context.get('request')
          user = get_object_or_404(User, pk=request.headers.get('UserID'))
          team = instance
          try:
               TeamLike.objects.get(user=user, team=team)
               return True
          except:
               return False
          
     def get_date_status(self, obj):
          return obj.date_status
     
          
     def to_representaation(self, instance):
          data = super().to_representaation(instance)
          members = get_team_members_with_creator_first(instance)
          data['members'] = members
          return data
          
class TeamSimpleDetailSerializer(serializers.ModelSerializer):  
     positions = serializers.StringRelatedField(many=True)
     member_cnt = serializers.SerializerMethodField()
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     date_status = serializers.SerializerMethodField()

     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'activity',
               'interest',
               'keywords', 
               'date_status',
               'member_cnt',
               'positions'
          ]
          
     def get_member_cnt(self, obj):
          return obj.member_cnt
     def get_date_status(self, obj):
          return obj.date_status

class TeamBeforeUpdateDetailSerializer(serializers.ModelSerializer):  
     positions = TeamPositionDetailSerializer(many=True, source='teampositions_set')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'short_pr', 
               'keywords',
               'activity',
               'interest',
               'cities',
               'meet_preference',
               'long_pr',
               'active_startdate',
               'active_enddate',
               'recruit_startdate',
               'recruit_enddate',
               'positions'
          ]  

class MyTeamSimpleDetailSerializer(serializers.ModelSerializer):
     positions = serializers.StringRelatedField(many=True)
     member_cnt = serializers.SerializerMethodField()
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     notification_status = serializers.SerializerMethodField()
     active = serializers.SerializerMethodField()
     
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'active',
               'activity',
               'interest',
               'keywords', 
               'notification_status',
               'member_cnt',
               'positions'
          ]
          
     def get_member_cnt(self, obj):
          return obj.member_cnt
     def get_notification_status(self, instance):
          return get_object_or_404(TeamMembers, team=instance, user=self.context.get('user')).noti_unread_cnt > 0
     def get_active(self, obj):
          today = date.today()
          active_enddate = date.fromisoformat(obj.active_enddate)
          return True if (active_enddate - today).days >= 0 else False
     
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
     

class TeamApplicationDetailSerializer(serializers.ModelSerializer):
     team = serializers.StringRelatedField()
     applicant = serializers.StringRelatedField()
     position = serializers.StringRelatedField()
     class Meta:
          model = TeamApplication
          fields = '__all__'

# list serializers
class TeamLikesListSerializer(serializers.ListSerializer):
     child = TeamSimpleDetailSerializer()
     class Meta:
          model = Team
          fields = '__all__'