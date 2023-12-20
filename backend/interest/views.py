from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import Interest
from .serializers import *

# Create your views here.
class InterestDetailAPIView(generics.RetrieveAPIView):
     queryset = Interest.objects.all()
     serializer_class = InterestSerializer
     lookup_field = 'name'
     
     def get_object(self):
          print(self.kwargs)
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()

class InterestListAPIView(generics.ListAPIView):
     queryset = Interest.objects.all().order_by('id')
     serializer_class = InterestSerializer