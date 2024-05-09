from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from django.db import transaction

from .models import *
from .serializers import *
from .permissions import *
from .exceptions import *
from team.utils import get_team_by_pk, get_member_by_team_and_user
from fcm_notification.utils import send_fcm_to_user

@permission_classes([IsTeamMemberPermission])
class TeamPostListCreateAPIView(generics.ListCreateAPIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          super().initial(request, *args, **kwargs)
          
     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.user
          return context
     
     def get_serializer_class(self):
          if self.request.method == 'POST':
               return TeamPostCreateUpdateSerializer
          elif self.request.method == 'GET':
               return TeamPostSimpleDetailSerializer
     
     def get_queryset(self):
          return TeamPost.objects.filter(post_to=self.team)


     def post(self, request, *args, **kwargs):
          member = TeamMembers.objects.get(team=self.team, user=self.user)
          request.data['writer'] = member.pk
          request.data['post_to'] = self.team.pk
          return self.create(request, *args, **kwargs)

     def get(self, request, *args, **kwargs):
          return self.list(request, *args, **kwargs)

@permission_classes([IsTeamMemberPermission, IsTeamPostWriterPermission])
class TeamPostDetailAPIView(UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin, generics.GenericAPIView):
     queryset = TeamPost.objects.all()
     lookup_field = 'post_pk'

     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          try:
               self.team_post = self.team.posts.get(pk=self.kwargs.get('post_pk'))
          except:
               raise TeamPostNotFoundInTeam()
          super().initial(request, *args, **kwargs)
          
     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.user
          return context
     
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return TeamPostDetailSerializer
          return  TeamPostCreateUpdateSerializer
     
     def get_object(self):
          return self.team_post

     def delete(self, request, *args, **kwargs):
          return self.destroy(request, *args, **kwargs)
     
     def patch(self, request, *args, **kwargs):
          return self.partial_update(request, *args, **kwargs)
     
     def get(self, request, *args, **kwargs):
          return self.retrieve(request, *args, **kwargs)
     
@permission_classes([IsTeamMemberPermission])
class TeamPostCommenCreateAPIView(generics.CreateAPIView):
     serializer_class = TeamPostCommentCreateSerializer
     queryset = TeamPostComment.objects.all()
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          try:
               self.team_post = self.team.posts.get(pk=self.kwargs.get('post_pk'))
          except:
               raise TeamPostNotFoundInTeam()
          super().initial(request, *args, **kwargs)
          
     @transaction.atomic
     def post(self, request, *args, **kwargs):
          member = TeamMembers.objects.get(team=self.team, user=self.user)
          request.data['writer'] = member.pk
          request.data['comment_to'] = self.team_post.pk
          
          # send fcm notification to post writer if comment writer != post writer
          if self.team_post.writer != member:
               title = f'{self.team}팀 게시판'
               body = f'{member.user.name} 님이 내 글에 댓글을 남겼습니다.'
               data = {
                    "page": "team_post",
                    "team_pk": str(self.team.pk),
                    "team_name": self.team.name,
                    "post_pk": str(self.team_post.pk)
               }
               send_fcm_to_user(self.team_post.writer.user, title, body, data)
     
          return self.create(request, *args, **kwargs)

@permission_classes([IsTeamMemberPermission, IsTeamPostCommentWriterPermission])   
class TeamPostCommenDestroyAPIView(generics.DestroyAPIView):
     queryset = TeamPostComment.objects.all()
     lookup_field = 'comment_pk'
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          try:
               self.team_post = self.team.posts.get(pk=self.kwargs.get('post_pk'))
               self.comment = self.team_post.comments.get(pk=self.kwargs.get('comment_pk'))
          except TeamPost.DoesNotExist:
               raise TeamPostNotFoundInTeam()
          except TeamPostComment.DoesNotExist:
               raise TeamPostCommentNotFoundInTeam()
          super().initial(request, *args, **kwargs)
     
     def get_object(self):
          return self.comment

@permission_classes([IsTeamMemberPermission])
class TeamPostViewerListAPIView(generics.ListAPIView):
     serializer_class = MyTeamMemberDetailSerializer
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          try:
               self.team_post = self.team.posts.get(pk=self.kwargs.get('post_pk'))
          except:
               raise TeamPostNotFoundInTeam()
          super().initial(request, *args, **kwargs)
     
     def get_queryset(self):
          return self.team_post.viewed.all()

@permission_classes([IsTeamMemberPermission])
class ToggleViewedStatus(APIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          try:
               self.team_post = self.team.posts.get(pk=self.kwargs.get('post_pk'))
          except:
               raise TeamPostNotFoundInTeam()
          super().initial(request, *args, **kwargs)
          
     def put(self, request, *args, **kwargs):
          member = TeamMembers.objects.get(team=self.team, user=self.user)
          if member in self.team_post.viewed.all():
               self.team_post.viewed.remove(member)
               return Response({"message": "post unviewed"}, status=status.HTTP_204_NO_CONTENT)
          else:
               self.team_post.viewed.add(member)
               return Response({"message": "post viewed"}, status=status.HTTP_201_CREATED)