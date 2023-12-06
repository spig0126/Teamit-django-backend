from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.mixins import UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.views import APIView

from .models import *
from .serializers import *

class TeamPostListCreateAPIView(generics.ListCreateAPIView):
     def get_serializer_class(self):
          if self.request.method == 'POST':
               return TeamPostCreateUpdateSerializer
          elif self.request.method == 'GET':
               return TeamPostSimpleDetailSerializer
     
     def get_queryset(self):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          return team.posts.all()

     def dispatch(self, request, *args, **kwargs):
          self.team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          self.user = get_object_or_404(User, pk=request.headers.get('UserID'))
          return super().dispatch(request, *args, **kwargs)
          
     def post(self, request, *args, **kwargs):
          try:
               member = TeamMembers.objects.get(team=self.team, user=self.user)
          except:
               raise PermissionDenied("user not allowed to write post to this team")
          request.data['writer'] = member.pk
          return self.create(request, *args, **kwargs)

     def get(self, request, *args, **kwargs):
          if self.user not in self.team.members.all():
               raise PermissionDenied("user not allowed to view team's posts")
          return self.list(request, *args, **kwargs)

class TeamPostDetailAPIView(UpdateModelMixin, DestroyModelMixin, RetrieveModelMixin, generics.GenericAPIView):
     queryset = TeamPost.objects.all()

     def get_serializer_class(self):
          if self.request.method == 'GET':
               return TeamPostDetailSerializer
          return  TeamPostCreateUpdateSerializer
     
     def dispatch(self, request, *args, **kwargs):
          self.team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          self.user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          try:
               self.post = self.team.posts.get(pk=self.kwargs.get('post_pk'))
               self.member = TeamMembers.objects.get(team=self.team, user=self.user)
          except:
               raise PermissionDenied("user not allowed")
          return super().dispatch(request, *args, **kwargs) 

     def delete(self, request, *args, **kwargs):
          return self.destroy(request, *args, **kwargs)
     
     def patch(self, request, *args, **kwargs):
          return self.partial_update(request, *args, **kwargs)
     
     def get(self, request, *args, **kwargs):
          serializer = self.get_serializer(self.post)
          return Response(serializer.data, status=status.HTTP_200_OK)
     
class TeamPostCommenCreateAPIView(generics.CreateAPIView):
     serializer_class = TeamPostCommentCreateSerializer
     queryset = TeamPostComment.objects.all()
     
     def post(self, request, *args, **kwargs):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          try:
               post = team.posts.get(pk=self.kwargs.get('post_pk'))
               member = TeamMembers.objects.get(team=team, user=user)
          except:
               raise PermissionDenied("user not allowed")
          request.data['writer'] = member.pk
          request.data['comment_to'] = post.pk
          return self.create(request, *args, **kwargs)
     
class TeamPostCommenDestroyAPIView(generics.DestroyAPIView):
     queryset = TeamPostComment.objects.all()
     lookup_field = 'comment_pk'
     
     def delete(self, request, *args, **kwargs):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          try:
               post = team.posts.get(pk=self.kwargs.get('post_pk'))
               member = TeamMembers.objects.get(team=team, user=user)
          except:
               raise PermissionDenied("user not allowed")
          comment = get_object_or_404(TeamPostComment, pk=self.kwargs.get('comment_pk'))
          comment.delete()
          return Response(status=status.HTTP_204_NO_CONTENT)

class TeamPostLikesListAPIView(generics.ListAPIView):
     serializer_class = TeamMemberDetailSerializer
     
     def get_queryset(self):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          try:
               post = team.posts.get(pk=self.kwargs.get('post_pk'))
               member = TeamMembers.objects.get(team=team, user=user)
          except:
               raise PermissionDenied("user not allowed")
          return post.likes.all()
     
     def get(self, request, *args, **kwargs):
          return self.list(request, *args, **kwargs)


class TeamPostLikeUnlikeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          try:
               post = team.posts.get(pk=self.kwargs.get('post_pk'))
               member = TeamMembers.objects.get(team=team, user=user)
          except:
               raise PermissionDenied("user not allowed")
          if member in post.likes.all():
               post.likes.remove(member)
               return Response({"message": "post unliked"}, status=status.HTTP_204_NO_CONTENT)
          else:
               post.likes.add(member)
               return Response({"message": "post liked"}, status=status.HTTP_201_CREATED)