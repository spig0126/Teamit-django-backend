from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
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

class TeamPositionDetailAPIView(generics.ListAPIView):
     serializer_class = TeamPositionDetailSerializer
     lookup_field = 'team'
     
     def get_queryset(self):
          team = self.kwargs.get('team')
          return TeamPositions.objects.filter(team=team)
     

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

# etc
# class ApplyToTeamAPIView(APIView):
     