from firebase_admin import auth
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from .exceptions import *
from user.models import User

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
          # Get the skip_authentication attribute from the view
          skip_authentication = getattr(request, 'skip_authentication', False)
          if skip_authentication:
               return None
          # Access the Authorization header from the request
          authorization_header = request.headers.get('Authorization')
          if not authorization_header:
               raise NoAuthToken("auth token not provided")

          # Extract token
          token = None
          if authorization_header.startswith('Bearer '):
               token = authorization_header[len('Bearer '):]
          else:
               raise InvalidAuthTokenFormat()
          
          # Verify Firebase token 
          decoded_token = None
          try:
               decoded_token = auth.verify_id_token(token)
               uid = decoded_token.get('uid')
               
               # Fetch user based on the UID
               try:
                    user = User.objects.get(uid=uid)
               except User.DoesNotExist:
                    raise UserNotFoundWithAuthToken()
               
               return (user, None)
          except auth.ExpiredIdTokenError:
               raise ExpiredAuthToken()
          except auth.InvalidIdTokenError:
               raise InvalidAuthToken()
          except Exception:
               raise FirebaseError()
          
          return None