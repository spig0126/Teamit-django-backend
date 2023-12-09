from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from user.models import User
from .models import *
from .serializers import *

# detail views
class TeamNotificationListAPIView(APIView):
     def get(self, request):
          user = get_object_or_404(User, pk=int(request.headers.get('UserID')))
          team = get_object_or_404(Team, pk=request.data['team_id'])
          
          if user in team.members.all():
               notifications = team.notifications.all().order_by('-created_at')
               notifications.update(is_read=True)
               list_data = []
               for notification in notifications:
                    notification_data = TeamNotificationDetailSerializer(notification).data
                    list_data.append(notification_data)
               return Response(list_data, status=status.HTTP_200_OK)
          raise PermissionDenied("user is not allowed to view this team's notifications")
          
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