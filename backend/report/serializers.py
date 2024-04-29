from rest_framework import serializers

from .models import *

class ReasonField(serializers.Field):
     def to_internal_value(self, data):
          for key, value in ReasonType.choices:
               if value == data:
                    return key
          raise serializers.ValidationError("Invalid choice")
     
     def to_representation(self, obj):
          return dict(ReasonType.choices)[obj]

report_fields = ['reported', 'reason']

class UserReportDetailSerializer(serializers.ModelSerializer):
     reported = serializers.SlugRelatedField(slug_field='name', queryset=User.objects.all())
     reason = ReasonField()
     
     class Meta:
          model = UserReport
          fields = report_fields

class TeamReportDetailSerializer(serializers.ModelSerializer):
     reported = serializers.SlugRelatedField(slug_field='pk', queryset=Team.objects.all())
     reason = ReasonField()
     
     class Meta:
          model = TeamReport
          fields = report_fields

class TeamPostReportDetailSerializer(serializers.ModelSerializer):
     reported = serializers.SlugRelatedField(slug_field='pk', queryset=TeamPost.objects.all())
     reason = ReasonField()
     
     class Meta:
          model = TeamPostReport
          fields = report_fields

class TeamPostCommentReportDetailSerializer(serializers.ModelSerializer):
     reported = serializers.SlugRelatedField(slug_field='pk', queryset=TeamPostComment.objects.all())
     reason = ReasonField()
     
     class Meta:
          model = TeamPostCommentReport
          fields = report_fields

class UserReviewReportDetailSerializer(serializers.ModelSerializer):
     reported = serializers.SlugRelatedField(slug_field='pk', queryset=UserReview.objects.all())
     reason = ReasonField()
     
     class Meta:
          model = UserReviewReport
          fields = report_fields

class UserReviewCommentReportDetailSerializer(serializers.ModelSerializer):
     reported = serializers.SlugRelatedField(slug_field='pk', queryset=UserReviewComment.objects.all())
     reason = ReasonField()
     
     class Meta:
          model = UserReviewCommentReport
          fields = report_fields