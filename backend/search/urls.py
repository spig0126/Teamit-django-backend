from django.urls import path

from .views import *

urlpatterns = [
     path("user/record/", UserSearchHistoryRecordAPIView.as_view()),
     path("user/history/", UserSearchHistoryListAPIView.as_view()),
     path("user/history/delete/<int:pk>/", DeleteUserSearchHistoryAPIView.as_view()),
     path("team/record/", TeamSearchHistoryRecordAPIView.as_view()),
     path("team/history/", TeamSearchHistoryListAPIView.as_view()),
     path("team/history/delete/<int:pk>/", DeleteUserSearchHistoryAPIView.as_view()),
     
]