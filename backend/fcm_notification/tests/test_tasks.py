import pytest

from fcm_notification.models import Device
from fcm_notification.tasks import send_fcm_to_user_task
from user.models import User


@pytest.fixture
def real_test_user():
    return User.objects.get(name='여니여니')


@pytest.mark.django_db
def test_send_fcm_to_user_task(real_test_user):
    result = send_fcm_to_user_task(real_test_user, 'title', 'body', 'data')
    print(result)