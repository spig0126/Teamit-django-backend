from django.urls import path

from .views import *

urlpatterns = [
     path("", TeamCreateAPIView.as_view()),
]
