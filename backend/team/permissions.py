from rest_framework import permissions

from .models import TeamMembers


class IsTeamCreatorPermission(permissions.BasePermission):
    message = "permission denied because user is not team creator"

    def has_permission(self, request, view):
        if request.method in ('PUT', 'PATCH', 'DELETE', 'POST'):
            team = view.team
            return request.user == team.creator
        return True  # Allow GET requests


class IsTeamMemberPermission(permissions.BasePermission):
    message = "permission denied because user is not member of this team"

    def has_permission(self, request, view):
        team = view.team
        if request.user in team.members.all():
            return True
        else:
            return False


class IsThisTeamMemberPermission(permissions.BasePermission):
    message = "permission denied because user is not this member"

    def has_permission(self, request, view):
        member_pk = view.member_pk
        member = TeamMembers.objects.filter(pk=member_pk).first()
        if member.user == request.user:
            return True
        return False


class IsNotTeamMemberPermission(permissions.BasePermission):
    message = "permission denied because user is already member of this team"

    def has_permission(self, request, view):
        if request.method == 'POST':
            team = view.team
            if request.user not in team.members.all():
                return True
            else:
                return False
        return True  # Allow GET requests

# class IsTeamApplicant(permissions.BasePermission):
#     message = "permission denied because user is not team creator"

#     def has_permission(self, request, view):
#           team_id = view.kwargs.get('team_pk')
#           try:
#                team = Team.objects.get(pk=team_id)
#                if TeamApplication.objects.filter(team=team, applicant=request.user).exists():
#                     return True
#                return False
#           except Team.DoesNotExist:
#                return False
