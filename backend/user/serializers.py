from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from datetime import datetime
from django.db import transaction
from re import search

from .models import *
from position.models import Position
from position.serializers import *
from interest.models import Interest
from interest.serializers import *
from activity.serializers import *
from region.serializers import *

# field serializers
class UserAvatarImageField(serializers.Field):
     def to_internal_value(self, data):
          # Convert the signed url to image path
          try:
               match = search('avatars/([1-9]|10|11)\.png', data)
               return match.group(0)
          except:
               return f'avatars/1.png'
     
     def to_representation(self, value):
          return value

class UserBackgroundImageField(serializers.Field):
     def to_internal_value(self, data):
          # Convert the signed url to image path
          try:
               match = search('backgrounds/([1-9]|10|11)\.png', data)
               return match.group(0)
          except:
               return f'backgrounds/1.png'
          
     def to_representation(self, value):
          return value

class UserField(serializers.Field):
     def to_internal_value(self, data):
          # Convert user pk/name to user instance
          try:
               if isinstance(data, str):
                    user = User.objects.get(name=data)
               else:
                    user = User.objects.get(pk=data)
               return user
          except User.DoesNotExist:
               raise serializers.ValidationError("Invalid user name/pk")
          
     def to_representation(self, value):
          return value.name

class ImageSerializer(serializers.Serializer):
    url = serializers.CharField()
    
# create serializers
class UserCreateSerializer(serializers.ModelSerializer):
     avatar = UserAvatarImageField()
     background = UserBackgroundImageField()
     positions = PositionsField()
     interests = InterestsField()

     class Meta:
          model = User
          fields = [
               'id', 
               'uid',
               'name', 
               'avatar',
               'background',
               'positions',
               'interests'
          ]

class UserProfileCreateSerializer(serializers.ModelSerializer):
     user = UserCreateSerializer()
     activities = AcitivitiesField()
     cities = CitiesField()
     
     class Meta:
          model = UserProfile
          fields = [
               'user', 
               'activities', 
               'birthdate',
               'sex', 
               'short_pr',
               'cities'
          ]
     
     @transaction.atomic 
     def create(self, validated_data):
          user_data = validated_data.pop('user')
        
          # Create User instance using the nested UserSerializer
          user_serializer = UserCreateSerializer(data=user_data)
          if user_serializer.is_valid():
               user = user_serializer.save()
          else:
               raise serializers.ValidationError(user_serializer.errors)

          # Create UserProfile linked to the User
          validated_data['user'] = user
          user_profile = super().create(validated_data)

          return user_profile
     

# detail serializers
class UserSimpleDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = User
          fields = [
               'id',
               'name',
               'avatar',
               'background'
          ]

class UserDetailSerializer(serializers.ModelSerializer):
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'interests']

class UserProfileDetailSerializer(serializers.ModelSerializer):
     activities = serializers.StringRelatedField(many=True)
     cities = serializers.StringRelatedField(many=True)

     class Meta:
          model = UserProfile
          fields = [
               'visibility', 
               'birthdate',
               'sex', 
               'activities',
               'cities',
               'short_pr',
               'education',
               'keywords',
               'tools',
               'experiences',
               'certificates',
               'links'   
          ]
          
class UserWithProfileDetailSerializer(serializers.ModelSerializer):
     profile = UserProfileDetailSerializer(read_only=True)
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     likes = serializers.SerializerMethodField()
     friends = serializers.SerializerMethodField()
     blocked = serializers.SerializerMethodField()
     
     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'interests', 'likes', 'friends', 'blocked', 'profile']

     def get_likes(self, instance):
          viewer_user = self.context.get('viewer_user')
          viewed_user = instance
          try:
               UserLikes.objects.get(from_user=viewer_user, to_user=viewed_user)
               return True
          except:
               return False
     
     def get_friends(self, instance):
          viewer_user = self.context.get('viewer_user')
          viewed_user = instance
          if viewed_user in viewer_user.friends.all():
               return True
          elif FriendRequest.objects.filter(to_user=viewed_user, from_user=viewer_user, accepted=False).exists():
               return "pending"
          elif FriendRequest.objects.filter(to_user=viewer_user, from_user=viewed_user, accepted=False).exists():
               return "received"
          return False

     def get_blocked(self, instance):
          viewer_user = self.context.get('viewer_user')
          viewed_user = instance
          if viewer_user.blocked_users.filter(pk=viewed_user.pk).exists():
               return True
          return False

class MyProfileDetailSerializer(serializers.ModelSerializer):
     profile = UserProfileDetailSerializer(read_only=True)
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'interests', 'profile']

class RecommendedUserDetailSerializer(serializers.ModelSerializer):
     positions = serializers.StringRelatedField(many=True)
     keywords = serializers.SerializerMethodField()
     short_pr = serializers.SerializerMethodField()
     liked_cnt = serializers.SerializerMethodField()
     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'short_pr', 'keywords', 'liked_cnt']
     
     def get_keywords(self, instance):
          return instance.profile.keywords
     def get_short_pr(self, instance):
          return instance.profile.short_pr
     def get_liked_cnt(self, instance):
          return instance.liked_by.count()

class FriendRequestDetailSerializer(serializers.ModelSerializer):
     to_user = serializers.StringRelatedField()
     from_user = serializers.StringRelatedField()
     
     class Meta:
          model = FriendRequest
          fields = '__all__'

class LikedUserDetailSerialzier(serializers.ModelSerializer):
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     likes = serializers.SerializerMethodField()
     
     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'interests', 'likes']
          
     def get_likes(self, instance):
          viewer_user = self.context.get('viewer_user')
          viewed_user = instance
          try:
               UserLikes.objects.get(from_user=viewer_user, to_user=viewed_user)
               return True
          except:
               return False
 
 
         
# update serializers
class UserImageUpdateSerializer(serializers.ModelSerializer):
     avatar = UserAvatarImageField()
     background = UserBackgroundImageField()
     
     class Meta:
          model = User
          fields = [
               'avatar',
               'background'
          ]

     def to_representation(self, instance):
          return MyProfileDetailSerializer(instance).data
     
class UserUpdateSerializer(serializers.ModelSerializer):
     positions = PositionsField()
     interests = InterestsField()
     
     class Meta:
          model = User
          fields = [
               'name',
               'positions', 
               'interests'
          ]
     
class UserProfileUpdateSerializer(serializers.ModelSerializer):
     cities = CitiesField()
     activities = AcitivitiesField()
     
     class Meta:
          model = UserProfile
          fields = [
               'visibility', 
               'birthdate', 
               'sex', 
               'activities',
               'cities',
               'short_pr',
               'education',
               'keywords',
               'tools',
               'experiences',
               'certificates',
               'links'   
          ]

class UserWithProfileUpdateSerializer(serializers.ModelSerializer):
     profile = UserProfileUpdateSerializer()
     positions = PositionsField()
     interests = InterestsField()

     class Meta:
          model = User
          fields = [
               'name', 
               'avatar', 
               'positions', 
               'interests', 
               'profile'
          ]

     @transaction.atomic 
     def update(self, instance, validated_data):
          request_data = self.context.get('request').data
          profile_data = validated_data.pop('profile', None)
          user_data = validated_data

          positions = user_data.pop("positions", None)
          interests = user_data.pop("interests", None)
          activities = profile_data.pop("activities", None)
          cities = profile_data.pop("cities", None)

          if request_data['essential']:
               for attr, value in user_data.items():
                    setattr(instance, attr, value)
               if positions is not None:
                    instance.positions.set(positions)
               if interests is not None:
                    instance.interests.set(interests)
                    
          profile_instance = instance.profile
          for attr, value in profile_data.items():
               setattr(profile_instance, attr, value)
          if activities is not None:
               profile_instance.activities.set(activities)
          if cities is not None:
               profile_instance.cities.set(cities)
          
          instance.save()
          profile_instance.save()
          return instance
     
     def to_representation(self, instance):
          return MyProfileDetailSerializer(instance).data
     
# list serializers
class UserLikesListSerializer(serializers.ListSerializer):
     child = LikedUserDetailSerialzier()
     
     class Meta:
          model = User
          fields = '__all__'
