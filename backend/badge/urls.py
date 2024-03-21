from django.urls import path

from .views import *

urlpatterns = [
     path("", BadgeRetrieveAPIView.as_view()),
     path("attendance/", UpdateUserLastLoginTimeAPIView.as_view()),
     path("shared-profile/", UpdateSharedProfileCntAPIView.as_view()),
     path("viewed/", ViewChangedBadgeAPIView.as_view())
]