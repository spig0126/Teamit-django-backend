from django.urls import path

from .views import *

urlpatterns = [
     path("", TeamCreateAPIView.as_view()),
     path("like/", LikeTeamAPIView.as_view()),
     path("unlike/", UnlikeTeamAPIView.as_view()),
     path("likes/", UserTeamLikesListAPIView.as_view()),
     path("apply/", SendTeamApplicationAPIView.as_view()),
     path("accept/", AcceptTeamApplicationAPIView.as_view()),
     path("decline/", DeclineTeamApplicationAPIView.as_view()),
     path("destroy/", TeamDestroyAPIView.as_view()),
     path("invitation/decline/", UserDeclineTeamInvitationAPIView.as_view()),
     path("invitation/accept/", UserAcceptTeamInvitationAPIView.as_view()),
     path("leave/", LeaveTeamAPIVIew.as_view()),
     path("drop/", DropTeamMemberAPIVIew.as_view()),
     path("detail/<int:pk>/", TeamDetailAPIView.as_view()),
     path("detail/simple/<int:pk>/", TeamSimpleDetailAPIView.as_view()),
     path("update/<int:pk>/", TeamUpdateAPIView.as_view()),
     path("list/", TeamByActivityListAPIView.as_view()),
     path("<int:team>/positions/", TeamPositionListAPIView.as_view()),
     path("<int:team>/members/", TeamMemberListAPIView.as_view())
]
