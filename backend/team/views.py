from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import *
from .serializers import *

# Create views
class TeamCreateAPIView(generics.CreateAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamCreateSerializer
     
# detail views
class TeamDetailAPIView(generics.RetrieveAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamDetailSerializer
     

# list views
class TeamByActivityListAPIView(generics.ListAPIView):
     serializer_class = TeamSimpleDetailSerializer
     
     def get_queryset(self):
          activity = self.request.query_params.get('activity')
          if activity is not None:
               queryset = Team.objects.filter(activity=activity)
          else:
               queryset = Team.objects.all()
          return queryset