from django.urls import path

from .views import *

urlpatterns = [
     path("private/", PrivateChatRoomDetailAPIView.as_view(), name="create private chat room"),
     path("private/<int:pk>/", PrivateChatRoomNameUpdateAPIView.as_view(), name="update chatroom name")
]
