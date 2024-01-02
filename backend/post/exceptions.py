
from rest_framework import status
from rest_framework.exceptions import APIException

class TeamNotFoundWithPk(APIException):
     status_code = status.HTTP_404_NOT_FOUND
     default_detail = "team not found with provided pk"
     default_code = "team_not_found_with_pk"
     
class TeamMemberNotFound(APIException):
     status_code = status.HTTP_404_NOT_FOUND
     default_detail = "team member not found with provided team and user"
     default_code = "team_member_not_found"
     
class TeamPostNotFoundInTeam(APIException):
     status_code = status.HTTP_404_NOT_FOUND
     default_detail = "team post is not posted to this team"
     default_code = "team_post_not_found_in_team"

class TeamPostCommentNotFoundInTeam(APIException):
     status_code = status.HTTP_404_NOT_FOUND
     default_detail = "comment is not posted to this post"
     default_code = "comment_not_found_in_team"