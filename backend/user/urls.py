from django.urls import path

from .views import *

urlpatterns = [
     # user
     path("", UserWithProfileDetailAPIView.as_view()),
     path("recommended/", RecommendedUserListAPIView.as_view()),
     path("<int:pk>/", UserDetailAPIView.as_view()),
     path("images/", UserImageUpdateAPIView.as_view()),
     path("name/available/", CheckUserNameAvailability.as_view()),

     # user profile
     path("profiles/", UserWithProfileListAPIView.as_view()),
     path("<int:pk>/profile/", UserWithProfileRetrieveUpdateAPIView.as_view()), 
     
     # friends
     path("send-friend-request/", SendFriendRequestAPIView.as_view()),
     path("unsend-friend-request/", UnsendFriendRequestAPIView.as_view()),
     path("accept-friend-request/", AcceptFriendRequestAPIView.as_view()),
     path("decline-friend-request/", DeclineFriendRequestAPIView.as_view()),
     path("unfriend/", UnfriendUserAPIView.as_view()),
     path("friends/", UserFriendsListAPIView.as_view()),
     
     # likes
     path("<int:pk>/like/", LikeUnlikeAPIView.as_view()),
     path("likes/", UserLikesListAPIView.as_view()),
     
     # block
     path("<int:pk>/block/", BlockUnblockUserAPIView.as_view()),
     path("blocked/", BlockedUserListAPIView.as_view()),
     
     # serach
     path("search/", UserSearchAPIView.as_view()),
]
