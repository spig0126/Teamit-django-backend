from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, status, serializers
from rest_framework.views import APIView

from user.models import User
from user.serializers import UserSimpleDetailSerializer
# from team.serializers import TeamApplicantDetailSerializer
from .models import *
from .serializers import *

# detail views
class TeamNotificationListAPIView(APIView):
     def post(self, request):
          user = get_object_or_404(User, name=request.data['user'])
          team = get_object_or_404(Team, pk=request.data['team_id'])
          
          if user in team.members.all():
               notifications = team.notifications.all().order_by('-created_at')
               notifications.update(is_read=True)
               list_data = []
               for notification in notifications:
                    notification_data = TeamNotificationDetailSerializer(notification).data
                    list_data.append(notification_data)
               return Response(list_data, status=status.HTTP_200_OK)
          return Response({"error": "user is not a team member"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
          
class NotificationListAPIView(APIView):
     def post(self, request):
          user = get_object_or_404(User, name=request.data['user'])
          
          notifications = user.notifications.all().order_by('-created_at')
          notifications.update(is_read=True)
          list_data = []
          for notification in notifications:
               notification_data = NotificationDetailSerializer(notification).data
               list_data.append(notification_data)
          return Response(list_data, status=status.HTTP_200_OK)
               