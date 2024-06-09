from datetime import datetime
from django.shortcuts import get_object_or_404
from .models import TeamMembers, TeamLike, TeamApplication

class TeamMethodsMixin:
     def members(self, team, serializer):
          members = TeamMembers.objects.filter(team=team)
          creator = members.filter(user=team.creator).first()
          non_creator_members = members.exclude(pk=creator.pk)
          return [serializer(creator).data] + serializer(non_creator_members, many=True).data
     
     def likes(self, team):
          user = self.context.get('user')
          return TeamLike.objects.filter(user=user, team=team).exists()
     
     def blocked(self, team):
          user = self.context.get('user')
          return team in user.blocked_teams.all()
     
     def is_member(self, team):
          user = self.context.get('user')
          if user in team.members.all():
               return True
          if TeamApplication.objects.filter(applicant=user, team=team, date__lte=team.recruit_enddate, date__gte=team.recruit_startdate).exists():
               return None
          return False
     
     def has_new_team_notifications(self, team):
          return get_object_or_404(TeamMembers, team=team, user=self.context.get('user')).noti_unread_cnt > 0
     
     def active(self, team):
          return datetime.fromisoformat(team.active_enddate) > datetime.now()
     
     def last_post(self, team):
          try:
               return team.posts.latest().content
          except Exception:
               return None