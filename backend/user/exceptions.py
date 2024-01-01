
from rest_framework import status
from rest_framework.exceptions import APIException


class UserNotFoundWithName(APIException):
     status_code = status.HTTP_404_NOT_FOUND
     default_detail = "user not found with provided name"
     default_code = "user_not_found_with_name"