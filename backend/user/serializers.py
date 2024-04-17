from rest_framework import serializers
from django.db import transaction
from urllib.parse import urlparse

from .models import *
from position.models import Position
from position.serializers import *
from interest.models import Interest
from interest.serializers import *
from activity.serializers import *
from region.serializers import *
from home.serializers import ImageBase64Field
from profile_card.signals import user_created, user_updated

# field serializers
class UserAvatarImageField(serializers.Field):
     def to_internal_value(self, data):
          # Convert the signed url to image path
          try:
               parsed_url = urlparse(data)
               return parsed_url.path[1:]
          except:
               return 'avatars/1.png'
     
     def to_representation(self, value):
          return value

class UserBackgroundImageField(serializers.Field):
     def to_internal_value(self, data):
          # Convert the signed url to image path
          try:
               parsed_url = urlparse(data)
               return parsed_url.path[1:]
          except:
               return 'backgrounds/1.png'
          
     def to_representation(self, value):
          return value

#######################################################
class UserRelatedInstancesMixin:
     def delete_M2M_instances(self, instance, related_field_name):
          related_field = getattr(instance, related_field_name)
          related_field.clear()
     
     def delete_O2M_instances(self, instance, related_field_name):
          related_field = getattr(instance, related_field_name)
          related_field.all().delete()
          
     def create_M2M_with_priority(self, instance, field_name, related_model, data):
          for priority, foreign_key in enumerate(data):
               related_model.objects.create(
                    user=instance,
                    priority=priority,
                    **{field_name: foreign_key}
               )
     
     def create_O2M(self, instance, related_model, data):
          for d in data:
               related_model.objects.create(user_profile=instance, **d)
               
     def set_M2M_with_priority(self, instance, field_name, related_field_name, related_model, data):
          self.delete_M2M_instances(instance, related_field_name)
          self.create_M2M_with_priority(instance, field_name, related_model, data)
          
     def set_related_instances(self, instance, related_field_name, related_model, data):
          self.delete_O2M_instances(instance, related_field_name)
          self.create_O2M(instance, related_model, data)
          
#######################################################
class UserInterestSerializer(serializers.ModelSerializer):
     interest = serializers.StringRelatedField()
     class Meta:
          model = UserInterest
          fields = '__all__'
          
class UserPositionSerializer(serializers.ModelSerializer):
     position = serializers.StringRelatedField()
     class Meta:
          model = UserPosition
          fields = '__all__'

class UserActivitySerializer(serializers.ModelSerializer):
     activity = serializers.StringRelatedField()
     class Meta:
          model = UserActivity
          fields = '__all__'

class UserCitySerializer(serializers.ModelSerializer):
     city = serializers.StringRelatedField()
     class Meta:
          model = UserCity
          fields = '__all__'

#######################################################
class UserExperienceCreateSerializer(serializers.ModelSerializer):
     image = ImageBase64Field(write_only=True, required=False, allow_null=True)
     activity = serializers.SlugRelatedField(slug_field='name', queryset=Activity.objects.all())  
     
     class Meta:
          model = UserExperience
          fields = [
               'title',
               'image',
               'start_date',
               'end_date',
               'activity',
               'pinned'
          ]

class UserCreateSerializer(UserRelatedInstancesMixin, serializers.ModelSerializer):
     avatar = UserAvatarImageField()
     background = UserBackgroundImageField()
     positions = serializers.SlugRelatedField(slug_field='name', queryset=Position.objects.all(), many=True)
     interests = serializers.SlugRelatedField(slug_field='name', queryset=Interest.objects.all(), many=True)

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

     def create(self, validated_data):
          interests = validated_data.pop('interests')
          positions = validated_data.pop('positions')
          user = super().create(validated_data)
          self.create_M2M_with_priority(user, 'interest', UserInterest, interests)
          self.create_M2M_with_priority(user, 'position', UserPosition, positions)
          
          user_created.send(sender=self.__class__, instance=user)
          return user
     
class UserProfileCreateSerializer(UserRelatedInstancesMixin, serializers.ModelSerializer):
     user = UserCreateSerializer()
     activities = serializers.SlugRelatedField(slug_field='name', queryset=Activity.objects.all(), many=True)     
     cities = serializers.SlugRelatedField(slug_field='full_name', queryset=City.objects.all(), many=True)     
     
     class Meta:
          model = UserProfile
          fields = [
               'user', 
               'birthdate',
               'sex', 
               'short_pr',
               'cities',
               'activities', 
          ]
     
     @transaction.atomic 
     def create(self, validated_data):
          user_data = validated_data.pop('user')
          cities = validated_data.pop('cities')
          activities = validated_data.pop('activities')
          
          user_serializer = UserCreateSerializer(data=user_data)
          user_serializer.is_valid(raise_exception=True)
          user = user_serializer.save()
          user_profile = UserProfile.objects.create(user=user, **validated_data)
          
          self.create_M2M_with_priority(user_profile, 'city', UserCity, cities)
          self.create_M2M_with_priority(user_profile, 'activity', UserActivity, activities)

          return user_profile

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
          return UserLikes.objects.filter(from_user=viewer_user, to_user=instance).exists()
     
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
          return viewer_user.blocked_users.filter(pk=instance.pk).exists()

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
          return UserLikes.objects.filter(from_user=viewer_user, to_user=instance).exists()
     
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
     avatar = UserAvatarImageField()
     background = UserBackgroundImageField()
     
     class Meta:
          model = User
          fields = '__all__'

class UserProfileUpdateSerializer(UserRelatedInstancesMixin, serializers.ModelSerializer):
     cities = serializers.SlugRelatedField(slug_field='full_name', queryset=City.objects.all(), many=True)  
     activities = serializers.SlugRelatedField(slug_field='name', queryset=Activity.objects.all(), many=True)  
     experiences = UserExperienceCreateSerializer(many=True)
     
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
     
     @transaction.atomic
     def update(self, instance, validated_data):
          activities = validated_data.pop("activities", None)
          cities = validated_data.pop("cities", None)
          experiences = validated_data.pop("experiences", None)
          
          if activities is not None:
               self.set_M2M_with_priority(instance, 'activity', 'activities', UserActivity, activities)
          if cities is not None:
               self.set_M2M_with_priority(instance, 'city', 'cities', UserCity, cities)
          if experiences is not None:
               self.set_related_instances(instance, 'experiences', UserExperience, experiences)
          return super().update(instance, validated_data)

class UserWithProfileUpdateSerializer(UserRelatedInstancesMixin, serializers.ModelSerializer):
     profile = UserProfileUpdateSerializer()
     positions = serializers.SlugRelatedField(slug_field='name', queryset=Position.objects.all(), many=True)  
     interests = serializers.SlugRelatedField(slug_field='name', queryset=Interest.objects.all(), many=True)  
     essential = serializers.BooleanField(write_only=True)

     class Meta:
          model = User
          fields = [
               'essential',
               'name', 
               'avatar', 
               'positions', 
               'interests', 
               'profile'
          ]

     @transaction.atomic 
     def update(self, instance, validated_data):
          essential = validated_data.pop('essential', None)
          profile_data = validated_data.pop('profile', None)
          user_data = validated_data
          positions = user_data.pop("positions", None)
          interests = user_data.pop("interests", None)

          if essential:
               if positions is not None:
                    self.set_M2M_with_priority(instance, 'position', 'positions', UserPosition, positions)
                    user_updated.send(sender=self.__class__, instance=instance)
               if interests is not None:
                    self.set_M2M_with_priority(instance, 'interest', 'interests', UserInterest, interests)
                    user_updated.send(sender=self.__class__, instance=instance)

          profile_serializer = self.fields['profile']
          profile_serializer.update(instance.profile, profile_data)

          return super().update(instance, validated_data)
     
     # def to_representation(self, instance):
     #      return MyProfileDetailSerializer(instance).data
     
class UserLikesListSerializer(serializers.ListSerializer):
     child = LikedUserDetailSerialzier()
     
     class Meta:
          model = User
          fields = '__all__'
