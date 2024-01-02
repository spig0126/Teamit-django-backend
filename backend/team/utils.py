from .models import Team, TeamMembers
from .exceptions import TeamNotFoundWithPk, TeamMemberNotFound

def get_team_members_with_creator_first(team):
     members = team.members.all()
     creator = members.filter(pk=team.creator).first()
     members = [creator] + [member for member in members if member != creator]
     
     return members

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