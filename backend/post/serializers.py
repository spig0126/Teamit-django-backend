from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import *
from team.serializers import TeamMemberDetailSerializer
from user.models import User

# detail serializers
class TeamPostCommentDetailSerializer(serializers.ModelSerializer):
     writer = serializers.StringRelatedField()
     
     class Meta:
          model = TeamPostComment
          fields = [
               'id',
               'writer',
               'created_at',
               'content'
          ]

class TeamPostSimpleDetailSerializer(serializers.ModelSerializer):
     writer = TeamMemberDetailSerializer()
     comment_cnt = serializers.SerializerMethodField()
     like_cnt = serializers.SerializerMethodField()
     likes = serializers.SerializerMethodField()
     
     class Meta:
          model = TeamPost
          fields = [
               'id',
               'writer',
               'post_to',
               'created_at',
               'content',
               'comment_cnt',
               'like_cnt',
               'likes'
          ]
     
     def get_comment_cnt(self, obj):
          return obj.comments.count()
     def get_like_cnt(self, obj):
          return obj.like_cnt
     def get_likes(self, instance):
          request = self.context.get('request')
          user = get_object_or_404(User, pk=request.headers.get('UserID'))
          if instance.likes.filter(user=user):
               return True
          return False

class TeamPostDetailSerializer(serializers.ModelSerializer):
     writer = TeamMemberDetailSerializer()
     comment_cnt = serializers.SerializerMethodField()
     like_cnt = serializers.SerializerMethodField()
     comments = TeamPostCommentDetailSerializer(many=True)
     class Meta:
          model = TeamPost
          fields = [
               'id',
               'writer',
               'post_to',
               'created_at',
               'content',
               'comment_cnt',
               'like_cnt',
               'comments'
          ]
     def get_comment_cnt(self, obj):
          return obj.comments.count()
     def get_like_cnt(self, obj):
          return obj.like_cnt
# create serializer
class TeamPostCreateUpdateSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamPost
          fields = [
               'writer',
               'post_to',
               'created_at',
               'content',
          ]

class TeamPostCommentCreateSerializer(serializers.ModelSerializer):
     class Meta:
          model = TeamPostComment
          fields = [
               'writer',
               'comment_to',
               'created_at',
               'content'
          ]
