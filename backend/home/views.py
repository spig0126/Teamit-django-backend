from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.files.storage import default_storage

class ImageRetrieveAPIView(APIView):
     def get(self, request, *args, **kwargs):
          type = self.request.query_params.get('type', None)
          many = self.request.query_params.get('many', None)
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

               # Extract URLs of the images
               image_urls = {i: default_storage.url(f'{folder_path}{i}') for i in range(1, len(files) + 1)}
          else:
               image_urls[type] = f'{folder_path}{type}'

          return Response(image_urls, status=status.HTTP_200_OK)