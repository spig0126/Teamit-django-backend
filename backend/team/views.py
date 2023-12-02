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
     
     