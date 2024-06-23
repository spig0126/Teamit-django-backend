import json
import pytest

from team.serializers import MyTeamDetailSerializer
from tests.test_team.factories import TeamMemberFactory


def test_team_creation(team1):
    team_data = json.dumps(MyTeamDetailSerializer(team1).data, indent=4, ensure_ascii=False)
    print(team_data)


@pytest.mark.django_db
class TestTeamMembersModel():
    def test_properties(self, team1):
        member = TeamMemberFactory(team=team1)
        user = member.user

        assert member.avatar == user.avatar.url
        assert member.name == user.name

        member.custom_name = 'custom name'
        member.save()
        assert member.name == 'custom name'
        assert member.name != user.name
