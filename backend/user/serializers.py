from rest_framework import serializers, status
from rest_framework.response import Response
from datetime import datetime

from .models import *
from position.models import Position
from position.serializers import *
from interest.models import Interest
from interest.serializers import *
from activity.serializers import *
from region.serializers import *

# create serializers
class UserCreateSerializer(serializers.ModelSerializer):
     class Meta:
          model = User
          fields = [
               'id', 
               'name', 
               'avatar',
               'background'
          ]
          
class UserProfileCreateSerializer(serializers.ModelSerializer):
     user = UserCreateSerializer()
     positions = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     interests = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     activities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     cities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     
     class Meta:
          model = UserProfile
          fields = [
               'user', 
               'positions',
               'interests',
               'activities', 
               'birthdate',
               'sex', 
               'cities'
          ]
     
     def create(self, validated_data):
          # check if all fields were provided
          try:
               user_data = validated_data.pop('user')
               user_name = user_data['name']
               positions = validated_data.pop('positions')
               interests = validated_data.pop('interests')
               activities = validated_data.pop('activities')
               birthdate = validated_data['birthdate']
               sex = validated_data['sex']
               cities =  validated_data.pop('cities')
          except KeyError:
               raise serializers.ValidationError({"message": "not all required fields were provided"})

          #create user and set manytomanyfields
          user_instance = User.objects.create(**user_data)
          position_instances = []
          interest_instances = []
          try:
               for position in positions:
                    position_instances.append(Position.objects.get(name=position))
               for interest in interests:
                    interest_instances.append(Interest.objects.get(name=interest))
               user_instance.positions.set(position_instances)
               user_instance.interests.set(interest_instances)
          except Position.DoesNotExist:
               user_instance.delete()
               raise serializers.ValidationError({"positions": "certain position does not exist"})
          except Interest.DoesNotExist:
               user_instance.delete()
               raise serializers.ValidationError({"interests": "certain interest does not exist"})

          #create profile and set manytomanyfields
          profile_instance = UserProfile.objects.create(user=user_instance, **validated_data)
          activity_instances = []
          city_instances = []
          try:
               for activity in activities:
                    activity_instances.append(Activity.objects.get(name=activity))
               profile_instance.activities.set(activity_instances)
               for city in cities:
                    province_name, city_name = city.strip().split()
                    province = Province.objects.get(name=province_name).id
                    city_instances.append(City.objects.get(name=city_name, province=province))
               profile_instance.cities.set(city_instances)
               profile_instance.save()
          except Activity.DoesNotExist:
               user_instance.delete()
               profile_instance.delete()
               raise serializers.ValidationError({"activities": "certain activity does not exist"})
          except Province.DoesNotExist:
               user_instance.delete()
               profile_instance.delete()
               raise serializers.ValidationError({"province": "province does not exist"})
          except City.DoesNotExist:
               user_instance.delete()
               profile_instance.delete()
               raise serializers.ValidationError({"city": "city does not exist"})
               

          return profile_instance
     

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

     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'interests', 'profile']

class FriendRequestDetailSerializer(serializers.ModelSerializer):
     to_user = serializers.StringRelatedField()
     from_user = serializers.StringRelatedField()
     
     class Meta:
          model = FriendRequest
          fields = '__all__'

# update serializers
class UserProfileUpdateSerializer(serializers.ModelSerializer):
     activities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     cities = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     
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
     positions = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
     interests = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

     class Meta:
          model = User
          fields = [
               'id', 
               'name', 
               'avatar', 
               'notifications', 
               'positions', 
               'interests', 
               'profile'
          ]

     
     def update(self, instance, validated_data):
          request_data = self.context.get('request').data
          profile_instance = instance.profile
          if request_data['essential']:
               for attr, value in validated_data.items():
                    if attr == 'positions':
                         positions = value
                         position_instances = []
                         for position in positions:
                              position_instances.append(Position.objects.get(name=position))
                         instance.positions.set(position_instances)
                    elif attr == "interests":
                         interests = value
                         interest_instances = []
                         for interest in interests:
                              interest_instances.append(Interest.objects.get(name=interest))
                         instance.interests.set(interest_instances)
                    elif attr == "name":
                         instance.name = value
                    else:
                         for attr, value in validated_data['profile'].items():
                              if attr == "cities":
                                   cities = value
                                   city_instances = []
                                   for city in cities:
                                        province_name, city_name = city.strip().split()
                                        province = Province.objects.get(name=province_name).id
                                        city_instances.append(City.objects.get(name=city_name, province=province))
                                   profile_instance.cities.set(city_instances)
                              else:
                                   setattr(profile_instance, attr, value)
               instance.save()
          else:
               for attr, value in validated_data['profile'].items():
                    setattr(profile_instance, attr, value)
          profile_instance.save()
               
          return instance