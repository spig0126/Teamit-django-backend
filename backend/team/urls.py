from django.urls import path

from .views import *

urlpatterns = [
     path("", TeamCreateAPIView.as_view()),
     path("detail/<int:pk>/", TeamDetailAPIView.as_view()),
     path("list/", TeamByActivityListAPIView.as_view()),
     path("<int:team>/positions/", TeamPositionDetailAPIView.as_view())
]
