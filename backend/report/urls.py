from django.urls import path

from .views import *

urlpatterns = [
     path("users/", UserReportCreateAPIView.as_view()),
     path("teams/", TeamReportCreateAPIView.as_view()),
     path("teams/posts/", TeamPostReportCreateAPIView.as_view()),
     path("teams/posts/comments/", TeamPostCommentReportCreateAPIView.as_view()),
     path("reviews/", UserReviewReportCreateAPIView.as_view()),
     path("reviews/comments/", UserReviewCommentReportCreateAPIView.as_view()),
]
