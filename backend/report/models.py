from django.db import models

from user.models import User
from team.models import Team
from post.models import TeamPost, TeamPostComment

class Report(models.Model):
    REPORT_TYPE_CHOICES = (
        ('user', 'User'),
        ('team', 'Team'),
        ('team_post', "TeamPost"),
        ('team_post_comment', "TeamPostComment")
    )
    REASON_CHOICES = (
         ('inappropriate_content', '욕설/혐오 발언'),
         ('harassment', '성적인 수치심'),
         ('religious/political', '특정 종교/정치적 목적'),
         ('impersonation/fraud', '사칭/사기')
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reported_type = models.CharField(max_length=17, choices=REPORT_TYPE_CHOICES)
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reported_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reported_team_post = models.ForeignKey(TeamPost, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reported_team_post_comment = models.ForeignKey(TeamPostComment, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reason = models.CharField(max_length=21, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
          if self.reported_type == 'user':
               return f"Report to user {self.reported_user.pk} for {self.reason} on {self.created_at.date()}"
          elif self.reported_type == 'team':
               return f"Report to team {self.reported_team.pk} for {self.reason} on {self.created_at.date()}"
          elif self.reported_type == 'team_post':
               return f"Report to team post {self.reported_team_post.pk} for {self.reason} on {self.created_at.date()}"
          elif self.reported_type == 'team_post_comment':
               return f"Report to team post comment {self.reported_team_post_comment.pk} for {self.reason} on {self.created_at.date()}"