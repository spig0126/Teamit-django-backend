from rest_framework import generics

from .models import Activity
from .serializers import *

class ActivityListAPIView(generics.ListAPIView):
     queryset = Activity.objects.all().order_by('id')
     serializer_class = ActivitySerializer
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)