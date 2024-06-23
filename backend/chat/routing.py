from django.urls import path

from .status_consumers import *
from .private_consumers import *
from .team_consumers import *
from .inquiry_consumers import *

websocket_urlpatterns = [
    path("ws/private-chat/<str:chatroom_id>/", PrivateChatConsumer.as_asgi()),
    path("ws/team-chat/<str:chatroom_id>/", TeamChatConsumer.as_asgi()),
    path("ws/chat-status/", ChatStatusConsumer.as_asgi()),
    path("ws/inquiry-chat/<str:chatroom_id>/", InquiryChatConsumer.as_asgi()),
    path("ws/team-inquiry-status/<str:team_pk>/", TeamInquiryStatusConsumer.as_asgi()),

]
