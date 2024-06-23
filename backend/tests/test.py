import pytest

from tests.user.factories import UserFactory


@pytest.mark.django_db
def test_disable_algolia_indexing():
    user = UserFactory()
    print(user.pk)