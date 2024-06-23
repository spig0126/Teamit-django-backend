import pytest
from rest_framework.test import APIClient

from tests.test_team.factories import TeamFactory, TeamMemberFactory
from tests.test_user.factories import UserFactory
from tests.test_user.token_test import create_firebase_token


@pytest.fixture
def user1(db):
    return UserFactory()


@pytest.fixture
def team1(db, user1):
    return TeamFactory(creator=user1)


@pytest.fixture
def member1(db, team1):
    return TeamMemberFactory(team=team1)


@pytest.fixture
def badge1(db, user1):
    return user1.badge


@pytest.fixture
def user2(db):
    return UserFactory()


@pytest.fixture
def team2(db, user2):
    return TeamFactory(creator=user2)


@pytest.fixture
def api_client(user1):
    client = APIClient()
    token = create_firebase_token(user1.uid)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client
