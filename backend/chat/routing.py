from django.urls import path

from .consumers import *

websocket_urlpatterns = [
     path("ws/private-chat/<str:chatroom_id>/", PrivateChatConsumer.as_asgi()),
     path("ws/team-chat/<str:chatroom_id>/", TeamChatConsumer.as_asgi()),
     path("ws/chat-status/", ChatStatusConsumer.as_asgi()),
     path("ws/inquiry-chat/<str:chatroom_id>/", PrivateChatConsumer.as_asgi()),
]
