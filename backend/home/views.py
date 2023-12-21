from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.files.storage import default_storage

class ImageRetrieveAPIView(APIView):
     def get(self, request, *args, **kwargs):
          type = self.request.query_params.get('type', None)
          many = self.request.query_params.get('many', None) == 'true'
          image_urls = {}
          
          if type == 'onboardings':
               folder_path = 'ui/onboardings/'
          elif type == 'avatars':
               folder_path = 'avatars/'
          elif type == 'backgrounds':
               folder_path = 'backgrounds/'
          else:
               folder_path = 'ui/'
          
          if many:
               files = default_storage.listdir(folder_path)[1]
               image_urls = {i: default_storage.url(f'{folder_path}{i}.png') for i in range(1, len(files))}
          else:
               image_urls[type] = default_storage.url(f'{folder_path}{type}.png')

          return Response(image_urls, status=status.HTTP_200_OK)