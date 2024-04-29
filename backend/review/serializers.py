from rest_framework import serializers

from .models import *
from user.serializers import *

class ActivityChoiceField(serializers.Field):
     def to_representation(self, obj):
          # int -> str
          return dict(ActivityType.choices)[obj]

     def to_internal_value(self, data):
          # str -> int
          for key, value in ActivityType.choices:
               if value == data:
                    return key
          raise serializers.ValidationError("Invalid choice")

class UserReviewCommentCreateUpdateSerializer(serializers.ModelSerializer):
     review = serializers.SlugRelatedField(slug_field='pk', queryset=UserReview.objects.all(), required=False)
     
     class Meta:
          model = UserReviewComment
          fields = [
               'review',
               'content'
          ]
          
     def to_representation(self, instance):
          return UserReviewCommentDetailSerializer(instance).data
     
class UserReviewCommentDetailSerializer(serializers.ModelSerializer):
     user = serializers.StringRelatedField()
     
     class Meta:
          model = UserReviewComment
          fields = '__all__'

class UserReviewCreateUpdateSerializer(serializers.ModelSerializer):
     reviewee = serializers.SlugRelatedField(slug_field='name', queryset=User.objects.all())
     activity = ActivityChoiceField()
     star_rating = serializers.DecimalField(max_digits=2, decimal_places=1)
     content = serializers.CharField(required=False)
     keywords = serializers.SlugRelatedField(slug_field='content', many=True, queryset=UserReviewKeyword.objects.all(), required=False)
     
     class Meta:
          model = UserReview
          fields = [
               'reviewee',
               'activity',
               'star_rating',
               'content',
               'keywords',
          ]
          
     def to_representation(self, instance):
          return UserReviewDetailSerializer(instance).data
     
class UserReviewDetailSerializer(serializers.ModelSerializer):
     reviewer = UserMinimalWithAvatarBackgroundDetailSerializer()
     activity = serializers.CharField(source='get_activity_display')
     keywords = serializers.StringRelatedField(many=True)
     comment = UserReviewCommentDetailSerializer()

     class Meta:
          model = UserReview
          fields = [
               'id',
               'reviewer',
               'timestamp',
               'activity',
               'star_rating',
               'content',
               'keywords',
               'comment',
               'edited'
          ]

