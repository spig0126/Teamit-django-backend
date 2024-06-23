import pytest

from search.models import UserSearchHistory, TeamSearchHistory
from tests.test_team.factories import TeamFactory
from tests.test_user.factories import UserFactory


@pytest.mark.django_db
class TestUserSearchHistoryModel():
    def test_search_history_max_30(self):
        user = UserFactory()
        for _ in range(35):
            searched_user = UserFactory()
            print(UserSearchHistory.objects.create(user=user, search_query='', searched_user=searched_user))

        assert UserSearchHistory.objects.filter(user=user).count() == 30
        print(UserSearchHistory.objects.filter(user=user).all())

@pytest.mark.django_db
class TestTeamSearchHistoryModel():
    def test_search_history_max_30(self):
        user = UserFactory()
        for _ in range(35):
            searched_team = TeamFactory()
            print(TeamSearchHistory.objects.create(user=user, search_query='', searched_team=searched_team))

        assert TeamSearchHistory.objects.filter(user=user).count() == 30
        print(TeamSearchHistory.objects.filter(user=user).all())

