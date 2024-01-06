from django.urls import path

from .views import *

urlpatterns = [
     path("user/record/", UserSearchHistoryRecordAPIView.as_view()),
     path("user/history/", SearchedUserHistoryListAPIView.as_view()),
     path("user/history/delete/<int:pk>/", DeleteUserSearchHistoryAPIView.as_view()),
     path("team/record/", TeamSearchHistoryRecordAPIView.as_view()),
     path("team/history/", SearchedTeamHistoryListAPIView.as_view()),
     path("team/history/delete/<int:pk>/", DeleteTeamSearchHistoryAPIView.as_view()),
     
]