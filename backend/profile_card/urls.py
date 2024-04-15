from django.urls import path

from .views import *

urlpatterns = [
     path("", ProfileCardRetrieveUpdateAPIView.as_view(), name="update profile card/ retreive info for profile card udpate page"),
     path("<str:name>/",  ProfileCardRetrieveAPIView.as_view(), name="retrieve profile card info"),
]