from django.db import models

from user.models import User
from team.models import Team
from post.models import TeamPost, TeamPostComment
from review.models import UserReview, UserReviewComment

class ReasonType(models.IntegerChoices):
     INAPPROPRIATE_CONTENT = 1, '욕설/혐오 발언'
     HARASSMENT = 2, '성적인 수치심'
     RELIGIOUS_POLITICAL = 3, '특정 종교/정치적 목적'
     IMPERSONATION_FRAUD = 4, '사칭/사기'
     
class UserReport(models.Model):
     reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='written_user_reports')
     reported = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_reports')
     reason = models.CharField(max_length=21, choices=ReasonType.choices)
     created_at = models.DateTimeField(auto_now_add=True)

class TeamReport(models.Model):
     reporter = models.ForeignKey(User, on_delete=models.CASCADE)
     reported = models.ForeignKey(Team, on_delete=models.CASCADE)
     reason = models.CharField(max_length=21, choices=ReasonType.choices)
     created_at = models.DateTimeField(auto_now_add=True)

class TeamPostReport(models.Model):
     reporter = models.ForeignKey(User, on_delete=models.CASCADE)
     reported = models.ForeignKey(TeamPost, on_delete=models.CASCADE)
     reason = models.CharField(max_length=21, choices=ReasonType.choices)
     created_at = models.DateTimeField(auto_now_add=True)

class TeamPostCommentReport(models.Model):
     reporter = models.ForeignKey(User, on_delete=models.CASCADE)
     reported = models.ForeignKey(TeamPostComment, on_delete=models.CASCADE)
     reason = models.CharField(max_length=21, choices=ReasonType.choices)
     created_at = models.DateTimeField(auto_now_add=True)

class UserReviewReport(models.Model):
     reporter = models.ForeignKey(User, on_delete=models.CASCADE)
     reported = models.ForeignKey(UserReview, on_delete=models.CASCADE)
     reason = models.CharField(max_length=21, choices=ReasonType.choices)
     created_at = models.DateTimeField(auto_now_add=True)

class UserReviewCommentReport(models.Model):
     reporter = models.ForeignKey(User, on_delete=models.CASCADE)
     reported = models.ForeignKey(UserReviewComment, on_delete=models.CASCADE)
     reason = models.CharField(max_length=21, choices=ReasonType.choices)
     created_at = models.DateTimeField(auto_now_add=True)