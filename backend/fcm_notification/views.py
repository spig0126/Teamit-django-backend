from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from .models import Device
from .serializers import DeviceSerializer
from .utils import *
from user.models import User
from team.models import Team

class DeviceListCreateView(generics.ListCreateAPIView):
     queryset = Device.objects.all()
     serializer_class = DeviceSerializer
     
     def create(self, request, *args, **kwargs):
          # Extract user and token data from the request
          user = request.user
          token = request.data.get('token')
          
          try:
               # update timestamp if token exists
               instance = Device.objects.get(user=user, token=token)
               instance.save()
               serializer = self.get_serializer(instance)
               return Response(serializer.data, status=status.HTTP_200_OK)
          except Device.DoesNotExist:
               # if not exist, create token
               request.data['user'] = user.pk
               serializer = self.get_serializer(data=request.data)
               serializer.is_valid(raise_exception=True)
               serializer.save()
               return Response(serializer.data, status=status.HTTP_201_CREATED)

class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
     queryset = Device.objects.all()
     serializer_class = DeviceSerializer
     lookup_field = 'token'
     
     def get_object(self):
          token = self.kwargs.get(self.lookup_field)
          device = get_object_or_404(Device, token=token)
          if device.user != self.request.user:
               raise PermissionDenied('this token does not belong to this user')
          return device
     
class TestAPIView(APIView):
     def get(self, request, *args, **kwargs):
          # user = User.objects.get(pk=3)
          # team = Team.objects.get(pk=76)
          # devices = get_team_members_devices(team)
          # for device in devices:
          #      print(device)
          #      check_device_token_freshness(device)
               
          # send fcm notification
          title = 'test title'
          body = f'test body'
          data = {
               "page": "test",
               # "sender_team": {
               #      "id": team.pk,
               #      "name": team.name
               # },
               # "team_application": {
               #      "id": team_application.pk,
               #      "position": team_application.position,
               #      "accepted": True
               # }
          }
          send_fcm_to_user(request.user, title, body, data)
          return Response(status=status.HTTP_200_OK)
