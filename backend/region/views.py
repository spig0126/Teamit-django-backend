from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.decorators import api_view

from .models import City, Province
from .serializers import CitySerializer, ProvinceSerializer

# Create your views here.
# @api_view(["GET"])
# def region_all(request, *args, **kwargs):
#      data = {}
#      for province in Province.objects.all():
#           data[province.name] = []
#           for city in City.objects.filter(province_id=province.id).all():
#                data[province.name].append(city.name)
#      print(data)
#      return Response(data)

class CityListAPIView(generics.ListAPIView):
     queryset = City.objects.all()
     serializer_class = CitySerializer
     
class CityDetailAPIView(generics.RetrieveAPIView):
     queryset = City.objects.all()
     serializer_class = CitySerializer
     lookup_field = 'name'
     
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
     
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()

