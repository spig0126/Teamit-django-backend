from django.urls import path

from .views import *

urlpatterns = [
     path("team/", TeamNotificationListAPIView.as_view()),
]
