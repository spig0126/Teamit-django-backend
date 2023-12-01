from django.urls import path, include

from .views import *

urlpatterns = [
     path("<int:pk>/", PositionDetailAPIView.as_view()),
     path("<str:name>/", PositionDetailAPIView.as_view()),
]
