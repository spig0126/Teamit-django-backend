from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

from .serializers import *

class BadgeRetrieveAPIView(generics.RetrieveAPIView):
     serializer_class = BadeDetailSerializer
     queryset = Badge.objects.all()
     
     def get_object(self):
          user = self.request.user
          return Badge.objects.get(user=user)

class UpdateUserLastLoginTimeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          user = request.user
          badge = user.badge
          now = timezone.now()
          
          if badge.attendance_level < 3:
               if (now - user.last_login).days > 1:
                    badge.attendance_cnt = 0
                    badge.save()
               elif (now - user.last_login).days == 1:
                    badge.attendance_cnt += 1
                    badge.save()
               # badge가 몇개면 fcm 보내기 
          user.save()
          return Response(status=status.HTTP_200_OK)

class UpdateSharedProfileCntAPIView(APIView):
     def put(self, request, *args, **kwargs):
          user = request.user
          badge = user.badge
          if badge.shared_profile_level < 3:
               badge.shared_profile_cnt += 1
               badge.save()
               # badge가 몇개면 fcm 보내기 
          return Response(status=status.HTTP_200_OK)