from django.urls import path, include

from .views import *

urlpatterns = [
     path("<int:pk>/", ActivityDetailAPIView.as_view()),
     path("<str:name>/", ActivityDetailAPIView.as_view()),
     path("", ActivityListAPIView.as_view()),
]
