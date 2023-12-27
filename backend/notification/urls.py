from django.urls import path

from .views import *

urlpatterns = [
     path("team/<int:team_pk>/", TeamNotificationListAPIView.as_view()),
     path("", NotificationListAPIView.as_view()),
     path("unread/status/", UnreadNotificationsStatusAPIView.as_view()),
     
]
