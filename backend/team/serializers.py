from django.shortcuts import get_object_or_404
from rest_framework import serializers
from datetime import *
from django.db import transaction
from django.core.files.storage import default_storage
import base64
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

from .models import *
from position.models import *
from position.serializers import PositionsField, PositionField
from activity.models import *
from activity.serializers import ActivityField
from region.serializers import CitiesField
from interest.serializers import InterestField
from .utils import get_team_members_with_creator_first
from user.models import User

# field serializers
class ImageBase64Field(serializers.Field):
     def to_internal_value(self, data):
          # decode image 
          try: 
               image_data = base64.b64decode(data)
               
               # Create an InMemoryUploadedFile from image_data
               image_io = BytesIO(image_data)
               image_file = InMemoryUploadedFile(
                    image_io,
                    None,  # field_name
                    'main.png',  # file_name
                    'image/png',  # content_type
                    image_io.tell,  # size
                    None  # content_type_extra
               )
               return image_file
          except Exception as error:
               print("An exception occurred:", error)
               raise serializers.ValidationError("Invalid image format")
     
     def to_representation(self, value):
          return value


# create serializers
class TeamMemberCreateSerializer(serializers.ModelSerializer):
     position = PositionField()
     
     class Meta:
          model = TeamMembers
          fields = [
               'position',
               'background',
               'noti_unread_cnt'
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
     creator = TeamMemberCreateSerializer()
     image = ImageBase64Field(write_only=True)
     
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
          user = User.objects.get(pk=int(self.context.get('request').headers.get('UserID')))

          validated_data['creator'] = user
          team = super().create(validated_data)
          
          
          # add creator as team member and create team positions
          TeamMembers.objects.create(team=team, user=user, **creator_data)
          for position_data in positions_data:
               TeamPositions.objects.create(team=team, **position_data)
               
          # uploat image to S3, store image path in db
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
                    # uploat image to S3, store image path in db
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
               'cnt', 
          ]

class TeamMemberDetailSerializer(serializers.ModelSerializer):
     user = serializers.StringRelatedField(read_only=True)
     position = serializers.StringRelatedField(read_only=True)
     avatar = serializers.ReadOnlyField()
     class Meta:
          model = TeamMembers
          fields = [
               'id',
               'user',
               'position',
               'background',
               'avatar',
               'team'
          ]

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
               'image',
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
               'image',
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
               'image',
               'active',
               'activity',
               'interest',
               'notification_status',
               'member_cnt',
               'keywords'
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