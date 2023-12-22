from django.urls import path, include

from .views import *

urlpatterns = [
     path("", ReportUserOrTeamAPIView.as_view()),
]
