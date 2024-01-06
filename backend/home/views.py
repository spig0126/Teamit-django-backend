from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.files.storage import default_storage

from .utilities import fetch_user_info, generate_firebase_custom_token
from user.models import User

class ThirdPartyLoginView(APIView):
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
          
     def get(self, request):
          # Access the Authorization header from the request
          authorization_header = request.headers.get('Authorization')
          if not authorization_header:
               return Response({'detail': 'authorization header missing'}, status=status.HTTP_401_UNAUTHORIZED)

          # Check if the header has the "Bearer " prefix
          if authorization_header.startswith('Bearer '):
               # Extract the token by removing the "Bearer " prefix
               access_token = authorization_header[len('Bearer '):]
          else:
               # Handle the case when the header format is not as expected
               return Response({'detail': 'invalid authorization header format'}, status=status.HTTP_401_UNAUTHORIZED)
          
          # Get login type (naver/kakao)
          login_type = request.query_params.get('type', None)
          if not login_type:
               return Response({'detail': 'login type missing'}, status=status.HTTP_400_BAD_REQUEST) 
          
          # Get uid from access token based on login type
          user_info = fetch_user_info(access_token, login_type)
          if not user_info:
               return Response({'detail': 'failed to fetch user info from login provider'}, status=status.HTTP_404_NOT_FOUND)
          
          # Generate firebase custom token with uid
          custom_token = generate_firebase_custom_token(user_info, login_type)
          if not custom_token:
               return Response({'detail': 'failed to generate firebase custom token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
          
          # Return custom_token as response
          return Response({'custom_token': custom_token}, status=status.HTTP_200_OK)

class CheckUserWithUID(APIView):
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
     
     def post(self, request):
          try:
               User.objects.get(uid=request.data.get('uid'))
               return Response({'user_exists': True}, status=status.HTTP_200_OK)
          except User.DoesNotExist:
               return Response({'user_exists': False}, status=status.HTTP_200_OK)
               
          
class ImageRetrieveAPIView(APIView):
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
        
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