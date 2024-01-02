from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import Activity
from .serializers import *

# Create your views here.
class ActivityDetailAPIView(generics.RetrieveAPIView):
     queryset = Activity.objects.all()
     serializer_class = ActivitySerializer
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

class ActivityListAPIView(generics.ListAPIView):
     queryset = Activity.objects.all().order_by('id')
     serializer_class = ActivitySerializer
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)