from django.urls import path

from .views import *

urlpatterns = [
    path("", PositionListAPIView.as_view())
]
