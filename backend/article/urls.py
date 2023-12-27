from django.urls import path

from .views import *

urlpatterns = [
     path("", ArticleListAPIView.as_view()),
     path("events/", EventArticleListAPIView.as_view())
]
