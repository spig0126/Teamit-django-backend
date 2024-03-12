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
     
     def retrieve(self, request, *args, **kwargs):
          instance = self.get_object()
          serializer = self.get_serializer(instance)
          data = serializer.data
          result = self.transform_badge_data(data)
          return Response(result)

     def transform_badge_data(self, data):
          result = []
          for field_name, value in data.items():
               badge_name = '_'.join(field_name.split('_')[:-1])
               img = []
               if type(value) is bool:
                    img.append(default_storage.url(f'badges/{badge_name}.png'))
               else:
                    for i in range(1, 4):
                         img.append(default_storage.url(f'badges/{badge_name}/{i}.png'))

               result.append({
                    'title': BADGE_TITLES[badge_name],
                    'subtitle': BADGE_SUBTITLES[badge_name],
                    'name': BADGE_NAME[badge_name],
                    'level': value,
                    'img': img,
                    'level_description': BADGE_LEVEL_DESCRIPTION[badge_name]
               })
          return result
     
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