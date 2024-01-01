from rest_framework import status
from rest_framework.exceptions import APIException

class UserNotFoundWithAuthToken(APIException):
     status_code = status.HTTP_404_NOT_FOUND
     default_detail = "user not found with the provided auth token"
     default_code = "user_not_found_with_auth_token"
     
class NoAuthToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "authentication token not provided"
    default_code = "no_auth_token"

class InvalidAuthTokenFormat(APIException):
     status_code = status.HTTP_400_BAD_REQUEST
     default_detail = "invalid authenticaion token format. doesn't start with 'Bearer '"
     default_code = "invalid_token_format"
     
class ExpiredAuthToken(APIException):
     status_code = status.HTTP_403_FORBIDDEN
     default_detail = "expired token"
     default_code = "expired_token"

class InvalidAuthToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "invalid authentication token provided"
    default_code = "invalid_token"

class FirebaseError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "user provided with the auth token is not a valid Firebase user, it has no Firebase UID"
    default_code = "no_firebase_uid"