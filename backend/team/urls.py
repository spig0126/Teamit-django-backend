from django.urls import path

from .views import *

urlpatterns = [
     # team 
     path("", TeamListCreateAPIView.as_view(), name='create team, get list by activity, get my team list'), 
     path("recommended/", RecommendedTeamListAPIView.as_view(), name='get recommended team list'), 
     path("<int:team_pk>/", TeamDetailAPIView.as_view(), name='update, delete, retrieve team'),  
     path("<int:team_pk>/room/", MyTeamRoomDetailAPIView.as_view(), name='get my team room info'), 
     path("<int:team_pk>/before/", TeamBeforeUpdateDetailAPIView.as_view()),  
     path("<int:team_pk>/positions/", TeamPositionListAPIView.as_view()),
     path("<int:team_pk>/unread/status/", HasUnreadTeamNotifications.as_view()),
     
     # team member       
     path("<int:team_pk>/members/", TeamMemberListCreateAPIView.as_view()),
     path("<int:team_pk>/members/decline/", TeamMemberDeclineAPIView.as_view()),
     path("<int:team_pk>/members/<int:member_pk>/", TeamMemberUpdateAPIView.as_view()),
     path("<int:team_pk>/members/<int:member_pk>/leave/", TeamMemberDestroyAPIView.as_view()),
     path("<int:team_pk>/members/<int:member_pk>/drop/", TeamMemberDropAPIView.as_view()),
     
     # team application
     path("<int:team_pk>/applications/", TeamApplicationListCreateAPIView.as_view()),
     path("<int:team_pk>/applications/<int:application_pk>/accept/", TeamApplicationAcceptAPIView.as_view()),
     path("<int:team_pk>/applications/<int:application_pk>/decline/", TeamApplicationDeclineAPIView.as_view()),
     
     # team like
     path("<int:team_pk>/like/", TeamLikeUnlikeAPIView.as_view()),
     path("likes/", UserTeamLikesListAPIView.as_view()),
     
     # team block
     path("<int:team_pk>/block/", BlockUnblockTeamAPIView.as_view()),
     path("blocked/", BlockedTeamListAPIView.as_view()),
     
     # permission
     path("<int:team_pk>/permission/", TeamPermissionUpdateAPIView.as_view(), name="permission_update"),
     path("<int:team_pk>/creator/<int:user_pk>/", UpdateTeamCreatorAPIView.as_view(), name="creator_update"),
     
     # search
     path("search/", TeamSearchAPIView.as_view())
     
]
