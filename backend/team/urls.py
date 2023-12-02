from django.urls import path

from .views import *

urlpatterns = [
     path("", TeamCreateAPIView.as_view()),
     path("detail/<int:pk>/", TeamDetailAPIView.as_view()),
]
