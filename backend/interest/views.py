from rest_framework import generics

from .models import Interest
from .serializers import *

class InterestListAPIView(generics.ListAPIView):
     queryset = Interest.objects.all().order_by('id')
     serializer_class = InterestSerializer
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)