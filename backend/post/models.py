from django.db import models

from team.models import TeamMembers, Team

class TeamPost(models.Model):
     writer = models.ForeignKey(TeamMembers, related_name='written_posts', null=True, on_delete=models.SET_NULL)
     post_to = models.ForeignKey(Team, related_name='posts', on_delete=models.CASCADE)
     created_at = models.DateTimeField(auto_now_add=True)
     content = models.TextField()
     viewed = models.ManyToManyField(
          TeamMembers,
          related_name="viewed_posts"
     )
     
     class Meta:
          ordering = ['-created_at']
          get_latest_by = '-created_at'
     
     @property
     def viewed_cnt(self):
          return self.viewed.count()


class TeamPostComment(models.Model):
     writer = models.ForeignKey(TeamMembers, related_name='written_comments', null=True, on_delete=models.SET_NULL)
     comment_to = models.ForeignKey(TeamPost, related_name='comments', on_delete=models.CASCADE)
     created_at = models.DateTimeField(auto_now_add=True)
     content = models.CharField()
     
     class Meta:
          ordering = ['created_at']
     