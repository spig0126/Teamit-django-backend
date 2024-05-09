from django.shortcuts import get_object_or_404
from rest_framework import serializers
from datetime import *
from django.db import transaction
from django.core.files.storage import default_storage
from django.db.models import Q

from home.serializers import ImageBase64Field
from .models import *
from position.models import *
from position.serializers import PositionField
from activity.models import *
from activity.serializers import ActivityField
from region.serializers import CitiesField
from interest.serializers import InterestField
from .utils import get_team_members_with_creator_first
from home.utilities import delete_s3_folder
from user.serializers import UserMinimalDetailSerializer

# create serializers
class TeamMemberCreateSerializer(serializers.ModelSerializer):
     position = PositionField()
     
     class Meta:
          model = TeamMembers
          fields = [
               'position',
               'background',
          ]

class TeamPositionCreateSerializer(serializers.ModelSerializer):
     position = PositionField()
     
     class Meta:
          model = TeamPositions
          fields = [
               'position',
               'pr',
               'cnt'
          ]

class TeamCreateUpdateSerializer(serializers.ModelSerializer):
     activity = ActivityField()
     interest = InterestField()
     cities = CitiesField()
     positions = TeamPositionCreateSerializer(many=True)
     creator = TeamMemberCreateSerializer()  # add creator as team member 
     image = ImageBase64Field(write_only=True, required=False, allow_null=True)
     
     class Meta: 
          model = Team
          fields = [
               'name', 
               'image',
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
               'recruit_enddate'
          ]

     @transaction.atomic 
     def create(self, validated_data):
          creator_data = validated_data.pop('creator', None)
          positions_data = validated_data.pop('positions', [])
          image = validated_data.pop('image', None)
          user = self.context['user']

          validated_data['creator'] = user
          team = super().create(validated_data)
          
          # create team positions
          TeamMembers.objects.create(team=team, user=user, **creator_data)
          for position_data in positions_data:
               TeamPositions.objects.create(team=team, **position_data)
               
          # uploat image to S3, store image path in db
          image_path = f'teams/default.png'
          if image is not None:
               image_path = f'teams/{team.pk}/main.png'
               default_storage.save(image_path, image)
               
          team.image = image_path
          team.save()
          
          return team
          
     @transaction.atomic 
     def update(self, instance, validated_data):
          for attr, value in validated_data.items():
               if attr == 'cities':
                    instance.cities.set(value)
               elif attr == 'positions':
                    instance.positions.clear()
                    for item in value:
                         TeamPositions.objects.create(team=instance, **item)
               elif attr == 'image':                    
                    if value == None:
                         # if image is none, set to default image
                         if instance.image == f'teams/{instance.pk}/main.png':
                              delete_s3_folder(f'teams/{instance.pk}/')
                         instance.image = f'teams/default.png'
                    else:
                         # upload image to S3, store image path in db
                         image_path = f'teams/{instance.pk}/main.png'
                         default_storage.save(image_path, value)
                         instance.image = image_path
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
               'cnt'
          ]

class TeamMemberDetailSerializer(serializers.ModelSerializer):
     user = UserMinimalDetailSerializer()
     position = PositionField()
     
     class Meta:
          model = TeamMembers
          fields = [
               'id',
               'name',
               'position',
               'background',
               'avatar',
               'team',
               'user'
          ]
          
class MyTeamMemberDetailSerializer(serializers.ModelSerializer):
     position = PositionField()
     user = UserMinimalDetailSerializer()
     
     class Meta:
          model = TeamMembers
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'position',
               'team',
               'user'
          ]

class MyTeamDetailSerializer(serializers.ModelSerializer):
     positions = TeamPositionDetailSerializer(many=True, source='recruiting')
     members = MyTeamMemberDetailSerializer(many=True, source='teammembers_set')
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
               'image',
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
     members = MyTeamMemberDetailSerializer(many=True, source='teammembers_set')
     last_post = serializers.SerializerMethodField()
     creator = UserMinimalDetailSerializer()
     has_new_team_notifications = serializers.SerializerMethodField()
     
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'has_new_team_notifications',
               'creator',
               'members',
               'last_post'
          ]  
          
     def get_has_new_team_notifications(self, instance):
          return get_object_or_404(TeamMembers, team=instance, user=self.context.get('user')).noti_unread_cnt > 0
     
     def get_last_post(self, instance):
          return instance.posts.latest().content
          
     def to_representation(self, instance):
          data = super().to_representation(instance)
          data['members'] = get_team_members_with_creator_first(data['members'])
          return data
     
class TeamDetailSerializer(serializers.ModelSerializer):
     creator = UserMinimalDetailSerializer()
     positions = TeamPositionDetailSerializer(many=True, source='recruiting')
     members = TeamMemberDetailSerializer(many=True, source='teammembers_set')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     is_member = serializers.SerializerMethodField()
     likes = serializers.SerializerMethodField()
     blocked = serializers.SerializerMethodField()
     
     class Meta:
          model = Team
          fields = [
               'id',
               'image',
               'name',
               'creator',
               'date_status',
               'likes',
               'is_member',
               'blocked',
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
          user = self.context.get('user')
          if user in instance.members.all():
               return True
          elif TeamApplication.objects.filter(applicant=user, team=instance).filter(Q(accepted__isnull=True) | Q(accepted=True)).exists():
               return None
          return False
     
     def get_likes(self, instance):
          user = self.context.get('user')
          team = instance
          return TeamLike.objects.filter(user=user, team=team).exists()

     def get_blocked(self, instance):
          user = self.context.get('user')
          team = instance
          return team in user.blocked_teams.all()
          
     def to_representation(self, instance):
          data = super().to_representation(instance)
          data['members'] = get_team_members_with_creator_first(data['members'])
          return data

class TeamSimpleDetailSerializer(serializers.ModelSerializer):  
     positions = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()

     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'image',
               'activity',
               'interest',
               'keywords', 
               'date_status',
               'member_cnt',
               'positions'
          ]
          
class TeamBasicDetailForChatSerializer(serializers.ModelSerializer):
     avatar = serializers.ImageField(source='image')
     background = serializers.SerializerMethodField()
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'avatar',
               'background'
          ]
     
     def get_background(self, obj):
          return ''
     
class SearchedTeamDetailSerializer(serializers.ModelSerializer):
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     likes = serializers.SerializerMethodField()

     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'image',
               'date_status',
               'likes',
               'activity',
               'interest',
               'keywords',
               'member_cnt',
               'member_and_position_cnt'
          ]

     def get_likes(self, instance):
          user = self.context.get('user')
          team = instance
          return TeamLike.objects.filter(user=user, team=team).exists()

class TeamBeforeUpdateDetailSerializer(serializers.ModelSerializer):  
     positions = TeamPositionDetailSerializer(many=True, source='recruiting')
     cities = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     class Meta:
          model = Team
          fields = [
               'id',
               'image',
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
     activity = serializers.StringRelatedField()
     has_new_team_notifications = serializers.SerializerMethodField()
     
     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'activity',
               'has_new_team_notifications',
               'member_cnt'
          ]

     def get_has_new_team_notifications(self, instance):
          return get_object_or_404(TeamMembers, team=instance, user=self.context.get('user')).noti_unread_cnt > 0

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
     
class LikedTeamDetailSerializer(serializers.ModelSerializer):
     positions = serializers.StringRelatedField(many=True)
     activity = serializers.StringRelatedField()
     interest = serializers.StringRelatedField()
     likes = serializers.SerializerMethodField()

     class Meta:
          model = Team
          fields = [
               'id',
               'name',
               'image',
               'activity',
               'interest',
               'keywords', 
               'date_status',
               'member_cnt',
               'likes',
               'positions',
          ]
          
     def get_likes(self, instance):
          user = self.context.get('user')
          team = instance
          return TeamLike.objects.filter(user=user, team=team).exists()


class TeamApplicationDetailSerializer(serializers.ModelSerializer):
     team = serializers.StringRelatedField()
     applicant = serializers.StringRelatedField()
     position = serializers.StringRelatedField()
     class Meta:
          model = TeamApplication
          fields = '__all__'

# list serializers
class TeamLikesListSerializer(serializers.ListSerializer):
     child = LikedTeamDetailSerializer()
     class Meta:
          model = Team
          fields = '__all__'
          
class TeamPermissionDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamPermission
          fields = '__all__'
     
