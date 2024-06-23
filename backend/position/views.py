from rest_framework import generics

from .models import *
from .serializers import *


class PositionListAPIView(generics.ListAPIView):
    queryset = Position.objects.all().order_by('id')
    serializer_class = PositionSerializer

    def initial(self, request, *args, **kwargs):
        request.skip_authentication = True
        super().initial(request, *args, **kwargs)
