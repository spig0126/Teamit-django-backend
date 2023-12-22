from django.shortcuts import get_object_or_404
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import render
from django.db import transaction
import requests

from .models import *
from .serializers import *
from user.models import User
from team.models import Team

class ReportUserOrTeamAPIView(generics.CreateAPIView):
     serializer_class = ReportDetailSerializer
     
     @transaction.atomic
     def create(self, request, *args, **kwargs):
          user_pk = request.headers.get('UserID', None)
          user = get_object_or_404(User, pk=user_pk)
          reported_type = request.data.get('reported_type', None)
          reported_team_pk = request.data.get('reported_team', None)
          reported_user_pk = request.data.get('reported_user_pk', None)
          block = request.data.pop('block', None)
          
          # abort if user is team's creator
          if reported_team_pk is not None:
               reported_team = get_object_or_404(Team, pk=reported_team_pk)
               if user == reported_team.creator:
                    raise PermissionDenied("User is not allowed to report this team. user is creator of team.")
          
          # abort if reported user isreported
          # if user_pk == 
          # add user instance to request data
          request.data['reporter'] = user_pk
          
          # create report
          serializer = self.get_serializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          report = serializer.save()
          
          # if block option is true, block user/team
          if block:
               if request.data['reported_type'] == 'user':
                    user.blocked_users.add(report.reported_user)
               else:
                    user.blocked_teams.add(report.reported_team)
          
          return Response(serializer.data, status=status.HTTP_201_CREATED)