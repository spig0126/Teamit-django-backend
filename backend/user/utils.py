from .models import User, FriendRequest
from .exceptions import *


def get_user_by_name(name):
    try:
        return User.objects.get(name=name)
    except User.DoesNotExist:
        raise UserNotFoundWithName()


def get_friend_request(from_user, to_user, accepted):
    try:
        return FriendRequest.objects.get(from_user=from_user, to_user=to_user, accepted=accepted)
    except FriendRequest.DoesNotExist:
        raise FriendRequestNotFound()
