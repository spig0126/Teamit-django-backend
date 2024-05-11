from django.urls import path

from .views import *

urlpatterns = [
     path("", UserWithProfileDetailAPIView.as_view(), name='create user / retrieve my profile'),
     
     # friends
     # path("send-friend-request/<str:name>/", SendFriendRequestAPIView.as_view()),
     # path("unsend-friend-request/<str:name>/", UnsendFriendRequestAPIView.as_view()),
     # path("accept-friend-request/<str:name>/", AcceptFriendRequestAPIView.as_view()),
     # path("decline-friend-request/<str:name>/", DeclineFriendRequestAPIView.as_view()),
     # path("unfriend/<str:name>/", UnfriendUserAPIView.as_view()),
     # path("friends/", UserFriendsListAPIView.as_view()),
     
     # search
     path("search/", UserSearchAPIView.as_view()),
     # path("search/friends/", FriendSearchAPIView.as_view()),
     
     # likes
     path("likes/", UserLikesListAPIView.as_view()),
     
     # block
     path("blocked/", BlockedUserListAPIView.as_view()),
     
     # user profile
     path("profiles/", UserWithProfileListAPIView.as_view(), name='get all users\' profiles'),

     # user
     path("recommended/", RecommendedUserListAPIView.as_view()),
     path("images/", UserImageUpdateAPIView.as_view()),
     path("name/available/", CheckUserNameAvailability.as_view()),
     path("update-info/", UpdatePageInfoRetrieveAPIView.as_view(), name='retrive info for profile update page'), 
     path("<str:name>/like/", LikeUnlikeAPIView.as_view()),
     path("<str:name>/profile/", UserWithProfileRetrieveUpdateAPIView.as_view(), name='update my profile / retrieve user profile'), 
     path("<str:name>/block/", BlockUnblockUserAPIView.as_view()),
     path("<str:name>/", UserDetailAPIView.as_view(), name='destroy user'),
]
