from .models import Team, TeamMembers
from .exceptions import TeamNotFoundWithPk, TeamMemberNotFound

def get_team_members_with_creator_first(team):
    members = TeamMembers.objects.filter(team=team)
    creator = members.filter(user=team.creator).values()
    members = members.exclude(user=team.creator).values()

    return list(creator) + list(members)

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