from django.urls import path, include

from .views import *

urlpatterns = [
    path("", InterestListAPIView.as_view())
]
