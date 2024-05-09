from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import *
from team.serializers import MyTeamMemberDetailSerializer
from user.models import User

# detail serializers
class TeamPostCommentDetailSerializer(serializers.ModelSerializer):
     writer = MyTeamMemberDetailSerializer()
     blocked_writer = serializers.SerializerMethodField()
     
     class Meta:
          model = TeamPostComment
          fields = [
               'id',
               'writer',
               'created_at',
               'blocked_writer',
               'content'
          ]
     
     def get_blocked_writer(self, instance):
          user = self.context.get('user')
          if instance.writer is not None and instance.writer.user in user.blocked_users.all():
               return True
          return False

class TeamPostSimpleDetailSerializer(serializers.ModelSerializer):
     writer = MyTeamMemberDetailSerializer()
     comment_cnt = serializers.SerializerMethodField()
     viewed_cnt = serializers.ReadOnlyField()
     viewed = serializers.SerializerMethodField()
     blocked_writer = serializers.SerializerMethodField()
     
     class Meta:
          model = TeamPost
          fields = [
               'id',
               'writer',
               'blocked_writer',
               'post_to',
               'created_at',
               'content',
               'comment_cnt',
               'viewed_cnt',
               'viewed'
          ]
     
     def get_comment_cnt(self, obj):
          return obj.comments.count()
     
     def get_viewed(self, instance):
          user = self.context.get('user')
          if instance.viewed.filter(user=user).exists():
               return True
          return False
     
     def get_blocked_writer(self, instance):
          user = self.context.get('user')
          if instance.writer is not None and instance.writer.user in user.blocked_users.all():
               return True
          return False

class TeamPostDetailSerializer(serializers.ModelSerializer):
     writer = MyTeamMemberDetailSerializer()
     comment_cnt = serializers.SerializerMethodField()
     viewed_cnt = serializers.ReadOnlyField()
     viewed = serializers.SerializerMethodField()
     comments = TeamPostCommentDetailSerializer(many=True)
     blocked_writer = serializers.SerializerMethodField()
     
     class Meta:
          model = TeamPost
          fields = [
               'id',
               'writer',
               'blocked_writer',
               'post_to',
               'created_at',
               'content',
               'comment_cnt',
               'viewed_cnt',
               'viewed',
               'comments'
          ]
          extra_kwargs = {
               'comments': {'source': 'get_ordered_comments'}
          }
     
     def get_ordered_comments(self, instance):
          return instance.comments.all().order_by('id')

     def get_comment_cnt(self, obj):
          return obj.comments.count()
     
     def get_viewed(self, instance):
          user = self.context.get('user')
          if instance.viewed.filter(user=user).exists():
               return True
          return False
     
     def get_blocked_writer(self, instance):
          user = self.context.get('user')
          if instance.writer is not None and instance.writer.user in user.blocked_users.all():
               return True
          return False


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
