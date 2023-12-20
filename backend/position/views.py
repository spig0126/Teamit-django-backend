from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import *
from .serializers import *

# Create your views here.
class PositionDetailAPIView(generics.RetrieveAPIView):
     queryset = Position.objects.all()
     serializer_class = PositionSerializer
     lookup_field = 'name'
     
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()
     
class PositionListAPIView(generics.ListAPIView):
     queryset = Position.objects.all().order_by('id')
     serializer_class = PositionSerializer


