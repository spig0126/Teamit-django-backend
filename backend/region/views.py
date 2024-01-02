from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.decorators import api_view

from .models import City, Province
from .serializers import *

class CityListAPIView(generics.ListAPIView):
     queryset = City.objects.all()
     serializer_class = CityWithProvinceSerializer

     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
          
class CityByProvinceListAPIView(generics.ListAPIView):
     queryset = Province.objects.all().order_by('id')
     serializer_class = ProvinceWithCitiesSerializer
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
          
class CityDetailAPIView(generics.RetrieveAPIView):
     queryset = City.objects.all()
     serializer_class = CityWithProvinceSerializer
     lookup_field = 'name'
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
          
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()

class ProvinceDetailAPIView(generics.RetrieveAPIView):
     queryset = Province.objects.all()
     serializer_class = ProvinceSerializer
     lookup_field = 'name'
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
          
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()

