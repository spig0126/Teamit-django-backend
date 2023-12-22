from django.db import models

from user.models import User
from team.models import Team

class Report(models.Model):
    REPORT_TYPE_CHOICES = (
        ('user', 'User'),
        ('team', 'Team')
    )
    REASON_CHOICES = (
         ('inappropriate_content', '욕설/혐오 발언'),
         ('harassment', '성적인 수치심'),
         ('religious/political', '특정 종교/정치적 목적'),
         ('impersonation/fraud', '사칭/사기')
    )

    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reported_type = models.CharField(max_length=4, choices=REPORT_TYPE_CHOICES)
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reported_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reason = models.CharField(max_length=21, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
          if self.report_user:
               return f"Report to user {self.reported_user.pk} for {self.reason} on {self.created_at.date()}"
          return f"Report to team {self.reported_team.pk} for {self.reason} on {self.created_at.date()}"