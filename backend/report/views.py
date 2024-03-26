from rest_framework import generics

from .models import *
from .serializers import *
from user.models import User
from team.models import Team

class ReportCreateAPIView(generics.CreateAPIView):
     def perform_create(self, serializer):
          user = self.request.user
          report = serializer.save(reporter=user)
          block = bool(self.request.query_params.get('block', ''))
          if block:
               reported_type = report._meta.get_field('reported').related_model
               try:
                    if reported_type == Team:
                         user.blocked_teams.add(report.reported)
                    elif reported_type in (TeamPost, TeamPostComment):
                         user.blocked_users.add(report.reported.writer.user)
                    elif reported_type == UserReview:
                         user.blocked_users.add(report.reported.reviewer)
                    elif reported_type == UserReviewComment:
                         user.blocked_users.add(report.reported.review.reviewee)
                    else:
                         user.blocked_users.add(report.reported)
               except AttributeError:
                    pass
               
class UserReportCreateAPIView(ReportCreateAPIView):
     serializer_class = UserReportDetailSerializer

class TeamReportCreateAPIView(ReportCreateAPIView):
     serializer_class = TeamReportDetailSerializer

class TeamPostReportCreateAPIView(ReportCreateAPIView):
     serializer_class = TeamPostReportDetailSerializer

class TeamPostCommentReportCreateAPIView(ReportCreateAPIView):
     serializer_class = TeamPostCommentReportDetailSerializer
     
class UserReviewReportCreateAPIView(ReportCreateAPIView):
     serializer_class = UserReviewReportDetailSerializer

class UserReviewCommentReportCreateAPIView(ReportCreateAPIView):
     serializer_class = UserReviewCommentReportDetailSerializer
