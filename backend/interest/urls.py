from django.urls import path, include

from .views import *

urlpatterns = [
     path("<int:pk>/", InterestDetailAPIView.as_view()),
     path("<str:name>/", InterestDetailAPIView.as_view()),
]
