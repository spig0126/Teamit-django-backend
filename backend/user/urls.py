from django.urls import path

from .views import *

urlpatterns = [
     path("", UserWithProfileCreateAPIView.as_view()),
     path("send-friend-request/", SendFriendRequestAPIView.as_view()),
     path("accept-friend-request/", AcceptFriendRequestAPIView.as_view()),
     path("profiles/", UserWithProfileListAPIView.as_view()),
     path("<int:pk>/", UserDetailAPIView.as_view()),
     path("<str:name>/", UserDetailAPIView.as_view()),
     path("delete/<int:pk>/", UserDestroyAPIView.as_view()),
     path("delete/<str:name>/", UserDestroyAPIView.as_view()),
     path("profile/<int:pk>/", UserWithProfileRetrieveUpdateAPIView.as_view()),
     path("profile/<str:name>/", UserWithProfileRetrieveUpdateAPIView.as_view()),
     path("name/available/", CheckUserNameAvailability.as_view()),
]
