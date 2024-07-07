from django.urls import path

from .views import *

urlpatterns = [
    path("old-messages/", OldChatMessageDestroyAPIView.as_view(), name="delete old messages"),
    path("private/", PrivateChatRoomDetailAPIView.as_view(), name="create/list private chat room"),
    path("private/<int:pk>/", PrivateChatRoomNameRetrieveUpdateAPIView.as_view(), name="update chatroom name"),

    path("inquiry/", InquiryChatRoomDetailAPIView.as_view(), name="create/list inquiry chat room"),
    path("inquiry/<int:pk>/", CheckUserIsInquirerAPIView.as_view(), name="cehck if user is inquirer or team"),

    path("team/<int:team_pk>/", TeamChatRoomDetailAPIView.as_view(), name="create/list team chat room"),
    path("team/<int:team_pk>/chatrooms/<int:chatroom_pk>/", TeamChatRoomUpdateAPIView.as_view(),
         name="create/list team chat room"),
    path("team/<int:chatroom_pk>/participants/", TeamChatRoomParticipantDetailAPIView.as_view(),
         name="list/create/destroy chatroom participants"),
    path("team/<int:chatroom_pk>/non-participants/", TeamChatRoomNonParticipantListAPIView.as_view(),
         name="list members that are not chatroom participants"),
]
