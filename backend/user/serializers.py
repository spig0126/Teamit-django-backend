from rest_framework import serializers
from django.db import transaction
from urllib.parse import urlparse
from django.core.files.storage import default_storage

from .models import *
from position.models import Position
from position.serializers import *
from interest.models import Interest
from interest.serializers import *
from activity.serializers import *
from region.serializers import *
from home.serializers import ImageBase64Field
from profile_card.signals import user_created, user_updated
from review.models import UserReviewKeyword

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
               if d.get('image', None) is None:
                    d.pop('image', None)
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

#####################CREATE SERIALIZERS##################################
class UserExperienceCreateSerializer(serializers.ModelSerializer):
     image = ImageBase64Field(write_only=True, required=False, allow_null=True)
     activity = serializers.SlugRelatedField(slug_field='name', queryset=Activity.objects.all())  
     
     class Meta:
          model = UserExperience
          fields = [
               'user_profile',
               'title',
               'image',
               'start_date',
               'end_date',
               'activity',
               'pinned'
          ]
     
     @transaction.atomic
     def create(self, validated_data):
          image = validated_data.pop('image', None)
          instance = super().create(validated_data)
          
          image_path = f'users/experience_default.png'
          if image is not None:
               image_path = f'users/{instance.user_profile.pk}/experiences/{instance.pk}.png'
               default_storage.save(image_path, image)
          instance.image = image_path
          instance.save()
          return instance
     
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

########################DETAIL SERIALIZERS##############################################
class UserExternalLinkDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = UserExternalLink
          fields = [
               'title',
               'url'
          ]

class UserMinimalDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = User
          fields = ['id', 'name']
     
class UserMinimalWithAvatarDetailSerializer(serializers.ModelSerializer):  
     class Meta:
          model = User
          fields = [
               'id',
               'name',
               'avatar',
          ]

class UserMinimalWithAvatarBackgroundDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = User
          fields = [
               'id',
               'name',
               'avatar',
               'background'
          ]

class UserSimpleDetailSerializer(serializers.ModelSerializer):
     main_position = serializers.StringRelatedField()
     birthdate = serializers.CharField(source='profile.birdthdate', read_only=True)
     sex = serializers.CharField(source='profile.sex', read_only=True)
     
     class Meta:
          model = User
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'main_position',
               'birthdate',
               'sex'
          ]

class UserDetailSerializer(serializers.ModelSerializer):
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     class Meta:
          model = User
          fields = ['id', 'name', 'avatar', 'background', 'positions', 'interests']

class UserExperienceDetailSerializer(serializers.ModelSerializer):
     activity = serializers.StringRelatedField()
     
     class Meta:
          model = UserExperience
          fields = ['title', 'image', 'start_date', 'end_date', 'activity', 'pinned']
          
class UserProfileDetailSerializer(serializers.ModelSerializer):
     activities = serializers.StringRelatedField(many=True)
     cities = serializers.StringRelatedField(many=True)
     experiences = serializers.SerializerMethodField()
     links = UserExternalLinkDetailSerializer(many=True)
     
     class Meta:
          model = UserProfile
          fields = [
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
     
     def get_experiences(self, instance):
          experiences = instance.experiences.order_by('-pinned', 'pk')
          return UserExperienceDetailSerializer(experiences, many=True).data
          
class UserWithProfileDetailSerializer(serializers.ModelSerializer):
     profile = UserProfileDetailSerializer(read_only=True)
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     likes = serializers.SerializerMethodField()
     blocked = serializers.SerializerMethodField()
     
     class Meta:
          model = User
          fields = [
               'id', 
               'name', 
               'avatar', 
               'background', 
               'positions', 
               'interests', 
               'likes', 
               'blocked', 
               'star_rating_average',
               'review_keywords',
               'profile',
     ]

     def get_likes(self, instance):
          viewer_user = self.context.get('viewer_user')
          return UserLikes.objects.filter(from_user=viewer_user, to_user=instance).exists()
     
     def get_blocked(self, instance):
          viewer_user = self.context.get('viewer_user')
          return viewer_user.blocked_users.filter(pk=instance.pk).exists()
     
     def to_representation(self, instance):
          representation = super().to_representation(instance)
          profile_representation = representation.pop('profile')
          return {**representation, **profile_representation}
     
class MyProfileDetailSerializer(serializers.ModelSerializer):
     profile = UserProfileDetailSerializer(read_only=True)
     interests = serializers.StringRelatedField(many=True)
     positions = serializers.StringRelatedField(many=True)
     
     class Meta:
          model = User
          fields = [
               'id', 
               'name', 
               'avatar', 
               'background', 
               'positions', 
               'interests', 
               'star_rating_average',
               'review_keywords',
               'profile'
          ]
     
     def to_representation(self, instance):
          representation = super().to_representation(instance)
          profile_representation = representation.pop('profile')
          return {**representation, **profile_representation}

class RecommendedUserDetailSerializer(serializers.ModelSerializer):
     short_pr = serializers.CharField(source='profile.short_pr')
     birthdate = serializers.CharField(source='profile.birthdate')
     sex = serializers.CharField(source='profile.sex')
     activities = serializers.StringRelatedField(many=True, source='profile.activities')
     positions = serializers.StringRelatedField(many=True)
     experiences = serializers.SerializerMethodField()
     likes = serializers.SerializerMethodField()
     
     class Meta:
          model = User
          fields = [
               'id', 
               'name', 
               'avatar', 
               'background', 
               'short_pr',
               'star_rating_average',
               'birthdate',
               'sex',
               'likes',
               'activities',
               'positions',
               'experiences'
          ]
     
     def get_likes(self, instance):
          viewer_user = self.context.get('viewer_user')
          return UserLikes.objects.filter(from_user=viewer_user, to_user=instance).exists()
     
     def get_experiences(self, instance):
          experiences = instance.profile.experiences.order_by('-pinned', 'pk')[:2]
          return UserExperienceDetailSerializer(experiences, many=True).data

class UserWithSameInterestDetailSerialzier(serializers.ModelSerializer):  
     main_activity = serializers.StringRelatedField()
     main_interest = serializers.StringRelatedField()
     class Meta:
          model = User
          fields = [
               'id',
               'name',
               'avatar',
               'background',
               'main_activity',
               'main_interest',
               'keywords'
          ]
          
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

##################UPDATE SERIALIZERS#######################
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
     links = UserExternalLinkDetailSerializer(many=True)
     
     class Meta:
          model = UserProfile
          fields = [
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
     
     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          for field_name, field in self.fields.items():
               field.allow_null = True
               
     @transaction.atomic
     def update(self, instance, validated_data):
          activities = validated_data.pop('activities', None)
          cities = validated_data.pop('cities', None)
          experiences = validated_data.pop('experiences', None)
          links = validated_data.pop('links', None)
          
          for attr, value in validated_data.items():
               if value is None:
                    continue
               if attr == 'activities':
                    self.set_M2M_with_priority(instance, 'activity', 'activities', UserActivity, activities)
               elif attr == 'cities':
                    self.set_M2M_with_priority(instance, 'city', 'cities', UserCity, cities)
               elif attr == 'links':
                    self.set_related_instances(instance, 'links', UserExternalLink, links)
               elif attr == 'experiences':
                    self.delete_O2M_instances(instance, 'experiences')
                    for experience in experiences:
                         experience['user_profile'] = instance
                         serializer = UserExperienceCreateSerializer(data=experience)
                         serializer.is_valid(raise_exception=True)
                         serializer.save()
               else:
                    setattr(instance, attr, value)
          instance.save()
          return instance

class UserWithProfileUpdateSerializer(UserRelatedInstancesMixin, serializers.ModelSerializer):
     profile = UserProfileUpdateSerializer()
     positions = serializers.SlugRelatedField(slug_field='name', queryset=Position.objects.all(), many=True, allow_null=True)  
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

     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          for field_name, field in self.fields.items():
               field.allow_null = True
               
     @transaction.atomic 
     def update(self, instance, validated_data):
          user_data = validated_data
          
          profile_data = user_data.pop('profile', None)
          profile_serializer = self.fields['profile']
          profile_serializer.update(instance.profile, profile_data)

          for attr, value in validated_data.items():
               if value is None:
                    continue
               if attr == 'positions':
                    self.set_M2M_with_priority(instance, 'position', 'positions', UserPosition, value)
                    user_updated.send(sender=self.__class__, instance=instance)
               elif attr == 'interests':
                    self.set_M2M_with_priority(instance, 'interest', 'interests', UserInterest, value)
                    user_updated.send(sender=self.__class__, instance=instance)
               else:
                    setattr(instance, attr, value)
          instance.save()
          return instance
     
     # def to_representation(self, instance):
     #      return MyProfileDetailSerializer(instance).data
     
class UserLikesListSerializer(serializers.ListSerializer):
     child = LikedUserDetailSerialzier()
     
     class Meta:
          model = User
          fields = '__all__'
