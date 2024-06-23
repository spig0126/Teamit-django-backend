from .models import Team, TeamMembers
from .exceptions import TeamNotFoundWithPk, TeamMemberNotFound


def get_team_members(team, serializer):
    members = TeamMembers.objects.filter(team=team)
    creator = members.filter(user=team.creator).first()
    non_creator_members = members.exclude(pk=creator.pk)
    creator_data = [serializer(creator).data]
    non_creator_members_data = serializer(non_creator_members, many=True).data
    return creator_data + non_creator_members_data


def get_team_by_pk(team_pk):
    try:
        return Team.objects.get(pk=team_pk)
    except Team.DoesNotExist:
        raise TeamNotFoundWithPk()


def get_member_by_team_and_user(team, user):
    try:
        return TeamMembers.objects.get(team=team, user=user)
    except TeamMembers.DoesNotExist:
        raise TeamMemberNotFound()


def get_member_by_pk(pk):
    try:
        return TeamMembers.objects.get(pk=pk)
    except TeamMembers.DoesNotExist:
        raise TeamMemberNotFound()
