from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from user.models import User
from .models import *
from .serializers import *
from team.models import TeamMembers

# detail views
class TeamNotificationListAPIView(generics.ListAPIView):
     serializer_class = TeamNotificationDetailSerializer
     
     def get_queryset(self):
          user = get_object_or_404(User, pk=int(self.request.headers.get('UserID')))
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          
          # check if user is team member
          try:
               member = TeamMembers.objects.get(team=team, user=user)
          except TeamMembers.DoesNotExist:
               raise PermissionDenied("user is not allowed to view this team's notifications")
          
          # update member's team notification reading status
          member.noti_unread_cnt = 0
          member.save()
          
          return team.notifications.all().order_by('-created_at')
          
class NotificationListAPIView(APIView):
     def get(self, request):
          user = get_object_or_404(User, pk=int(request.headers.get('UserID')))
          
          notifications = user.notifications.all().order_by('-created_at')
          notifications.update(is_read=True)
          list_data = []
          for notification in notifications:
               notification_data = NotificationDetailSerializer(notification).data
               list_data.append(notification_data)
          return Response(list_data, status=status.HTTP_200_OK)

class UnreadNotificationsStatusAPIView(APIView):
     def get(self, request):
          user = get_object_or_404(User, pk=int(request.headers.get('UserID')))
          
          if user.notifications.filter(is_read=False).exists():
               return Response({"unread": True}, status=status.HTTP_200_OK)
          return Response({"unread": False}, status=status.HTTP_200_OK)