from rest_framework import generics, status
from rest_framework.response import Response
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from .models import *
from .serializers import *
from user.serializers import UserDetailSerializer
from team.serializers import SearchedTeamDetailSerializer

class UserSearchHistoryRecordAPIView(generics.CreateAPIView):
     serializer_class = UserSearchHistoryDetailSerializer
     
     @transaction.atomic
     def create(self, request, *args, **kwargs):
          request.data['user'] = request.user.pk
          serializer = self.get_serializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          
          searched_user = serializer.data.get('searched_user')
          try:
               instance = UserSearchHistory.objects.get(user=request.user, searched_user=searched_user)
               instance.search_query = serializer.data.get('search_query')
          except UserSearchHistory.DoesNotExist:
               if searched_user in request.user.blocked_users.all().values_list('pk', flat=True):
                    return Response({'detail': 'cannot record search on blocked user'}, status=status.HTTP_400_BAD_REQUEST)
               instance = UserSearchHistory(**serializer.validated_data)
          instance.save()
          
          return Response(serializer.data, status=status.HTTP_200_OK)
               
class UserSearchHistoryListAPIView(generics.ListAPIView):
     serializer_class = UserSearchHistoryDetailSerializer
     
     def get_queryset(self):
          return UserSearchHistory.objects.filter(user=self.request.user).order_by('-timestamp')

class SearchedUserHistoryListAPIView(generics.ListAPIView):
     serializer_class = UserDetailSerializer
     
     def get_queryset(self):
          search_histories = UserSearchHistory.objects.filter(user=self.request.user).order_by('-timestamp')
          searched_users = [search_history.user for search_history in search_histories]
          return searched_users
 
class DeleteUserSearchHistoryAPIView(generics.DestroyAPIView):
     def get_queryset(self):
          return UserSearchHistory.objects.filter(user=self.request.user)

class TeamSearchHistoryRecordAPIView(generics.CreateAPIView):
     serializer_class = TeamSearchHistoryDetailSerializer
     
     @transaction.atomic
     def create(self, request, *args, **kwargs):
          request.data['user'] = request.user.pk
          serializer = self.get_serializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          
          searched_team = serializer.data.get('searched_team')
          try: 
               instance = TeamSearchHistory.objects.get(user=request.user, searched_team=searched_team)
               instance.search_query = serializer.data.get('search_query')
          except TeamSearchHistory.DoesNotExist:
               if searched_team in request.user.blocked_teams.all().values_list('pk', flat=True):
                    return Response({'detail': 'cannot record search on blocked team'}, status=status.HTTP_400_BAD_REQUEST)
               instance = TeamSearchHistory(**serializer.validated_data)
          instance.save()
          
          return Response(serializer.data, status=status.HTTP_200_OK)
     
class TeamSearchHistoryListAPIView(generics.ListAPIView):
     serializer_class = TeamSearchHistoryDetailSerializer
     
     def get_queryset(self):
          return TeamSearchHistory.objects.filter(user=self.request.user).order_by('-timestamp')

class SearchedTeamHistoryListAPIView(generics.ListAPIView):
     serializer_class = SearchedTeamDetailSerializer
     
     def get_queryset(self):
          search_histories = TeamSearchHistory.objects.filter(user=self.request.user).order_by('-timestamp')
          searched_teams = [search_history.searched_team for search_history in search_histories]
          return searched_teams
     
class DeleteTeamSearchHistoryAPIView(generics.DestroyAPIView):
     def get_queryset(self):
          return TeamSearchHistory.objects.filter(user=self.request.user)
