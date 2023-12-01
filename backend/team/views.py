from rest_framework import generics

from .models import *
from .serializers import *

# Create your views here.
class TeamCreateAPIView(generics.CreateAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamCreateSerializer