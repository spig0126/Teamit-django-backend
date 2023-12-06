from django.urls import path

from .views import *

urlpatterns = [
     # team 
     path("", TeamListCreateAPIView.as_view()),
     path("<int:pk>/", TeamDetailAPIView.as_view()),
     path("<int:pk>/positions/", TeamPositionListAPIView.as_view()),
     
     # team member 
     path("<int:team_pk>/members/", TeamMemberListCreateAPIView.as_view()),
     path("<int:team_pk>/members/decline/", TeamMemberDeclineAPIView.as_view()),
     path("<int:team_pk>/members/<int:member_pk>/leave/", TeamMemberDestroyAPIView.as_view()),
     path("<int:team_pk>/members/<int:member_pk>/drop/", TeamMemberDropAPIView.as_view()),
     
     # team application
     path("<int:team_pk>/applications/", TeamApplicationListCreateAPIView.as_view()),
     path("<int:team_pk>/applications/<int:application_pk>/accept/", TeamApplicationAcceptAPIView.as_view()),
     path("<int:team_pk>/applications/<int:application_pk>/decline/", TeamApplicationDeclineAPIView.as_view()),
     
     # team like
     path("<int:team_pk>/like/", TeamLikeUnlikeAPIView.as_view()),
     path("likes/", UserTeamLikesListAPIView.as_view()),
]
