import pytest

from tests.test_user.factories import UserFactory


@pytest.fixture
def user1(db):
    return UserFactory()
