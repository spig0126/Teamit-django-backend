from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

from .serializers import *
from .utils import *

class BadgeRetrieveAPIView(generics.RetrieveAPIView):
     serializer_class = BadeDetailSerializer
     
     def get_object(self):
          user = self.request.user
          return Badge.objects.get(user=user)

class ViewChangedBadgeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          badge = request.user.badge
          badge_keys = list(BADGE_TITLES.keys())
          badge_values = list(BADGE_TITLES.values())
          pos = badge_values.index(request.query_params.get('title', None))
          setattr(badge, f'{badge_keys[pos]}_change', False)
          badge.save()
          return Response(status=status.HTTP_200_OK)

class UpdateUserLastLoginTimeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          user = request.user
          badge = user.badge
          now = timezone.now()
          
          if badge.attendance_level < 3:
               if (now - user.last_login_time).days > 1:
                    badge.attendance_cnt = 0
                    badge.save()
               elif (now - user.last_login_time).days == 1:
                    before_level = badge.attendance_level
                    badge.attendance_cnt += 1
                    if before_level != badge.attendance_level:
                         badge.attendance_change = True
                         send_level_badge_fcm(request.user.pk, 'attendance', badge.attendance_level)
                    badge.save()
          return Response(status=status.HTTP_200_OK)

class SharedProfileAPIView(APIView):
     def put(self, request, *args, **kwargs):
          user = request.user
          badge = user.badge
          if not badge.shared_profile_status:
               badge.shared_profile_status = True
               badge.shared_profile_change = True
               badge.save()
               send_status_badge_fcm(request.user.pk, 'shared_profile')
          return Response(status=status.HTTP_200_OK)