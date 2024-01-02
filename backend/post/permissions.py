from rest_framework import permissions

from team.models import Team

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

class IsTeamPostWriterPermission(permissions.BasePermission):
     message = "permission denied because user is not writer of this team npost"
    
     def has_permission(self, request, view):
          if request.method in ('PUT', 'PATCH', 'DELETE'):
               team_post = view.team_post
               if request.user == team_post.writer.user:
                    return True
               else:
                    return False
          return True

class IsTeamPostCommentWriterPermission(permissions.BasePermission):
     message = "permission denied because user is not writer of this comment"
    
     def has_permission(self, request, view):
          if request.method in ('PUT', 'PATCH', 'DELETE'):
               comment = view.comment
               if request.user == comment.writer.user:
                    return True
               else:
                    return False
          return True