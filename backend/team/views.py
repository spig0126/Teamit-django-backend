from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response

from .models import *
from .serializers import *
from notification.models import *

# Create views
class TeamCreateAPIView(generics.CreateAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamCreateSerializer
     
# detail views
class TeamDetailAPIView(generics.RetrieveAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamDetailSerializer

# list views
class TeamMemberListAPIView(generics.ListAPIView):
     serializer_class = TeamMemberDetailSerializer
     lookup_field = 'team'
     
     def get_queryset(self):
          team = self.kwargs.get('team')
          return TeamMembers.objects.filter(team=team)
     
class TeamPositionListAPIView(generics.ListAPIView):
     serializer_class = TeamPositionDetailSerializer
     lookup_field = 'team'
     
     def get_queryset(self):
          team = self.kwargs.get('team')
          return TeamPositions.objects.filter(team=team)
     

class TeamByActivityListAPIView(generics.ListAPIView):
     serializer_class = TeamSimpleDetailSerializer
     
     def get_queryset(self):
          activity = self.request.query_params.get('activity')
          if activity is not None:
               queryset = Team.objects.filter(activity=activity)
          else:
               queryset = Team.objects.all()
          return queryset

# etc
class SendTeamApplicationAPIView(APIView):
     def post(self, request):
          data = request.data

          team = get_object_or_404(Team, id=data["team_id"])
          applicant = get_object_or_404(User, name=data["applicant"])
          position = get_object_or_404(Position, name=data["position"])
          
          if team.positions.filter(name=position.name).exists():
               if applicant not in team.members.all():
                    if not TeamApplication.objects.filter(applicant=applicant, team=team).exists():
                         team_application  = TeamApplication.objects.create(
                              team = team,
                              applicant = applicant,
                              position = position
                         )
                         serializer = TeamApplicationDetailSerializer(team_application)
                         return Response(serializer.data, status=status.HTTP_200_OK)
                    return Response({"message": "this team application already exists"}, status=status.HTTP_409_CONFLICT)   
               return Response({"message": "user is already a member of team"}, status=status.HTTP_400_BAD_REQUEST) 
          return Response({"message": "the position is already taken or doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
     
class AcceptTeamApplicationAPIView(APIView):
     def post(self, request):
          data = request.data
          
          team_application = get_object_or_404(TeamApplication, pk=data['team_application_id'])
          user = get_object_or_404(User, name=request.data['user'])
          team_application_notification = get_object_or_404(TeamNotification, related=team_application)
          team = team_application.team
          applicant = team_application.applicant
          
          team_application_instance = None
          team_application_notification_instance = None
          if user == team.creator:
               if not team_application.accepted:
                    try:
                         team_application.accepted = True
                         team_application_instance = team_application.save()
                         
                         # set application notification as read (just in case)
                         if not team_application_notification.is_read:
                              team_application_notification.is_read = True
                              team_application_notification_instance = team_application_notification.save()
                         
                         # create team_application_accepted notifcation for user
                         Notification.objects.create(
                              type="team_application_accepted",
                              to_user = applicant,
                              related_id = team_application_notification.pk
                         )
                         serializer = TeamApplicationDetailSerializer(team_application)
                         return Response(serializer.data, status=status.HTTP_200_OK)
                    except:
                         if team_application_instance is not None:
                              team_application_instance.delete()
                         if team_application_notification_instance is not None:
                              team_application_notification_instance.delete()
                         Response({"message": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
               return Response({"message": "this team application is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"message": "user is not the team's creator"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class DeclineTeamApplicationAPIView(APIView):
     def post(self, request):
          data = request.data
          
          team_application = get_object_or_404(TeamApplication, pk=data['team_application_id'])
          user = get_object_or_404(User, name=request.data['user'])
          team_application_notification = get_object_or_404(TeamNotification, related=team_application)
          team = team_application.team
          applicant = team_application.applicant
          
          team_application_instance = None
          team_application_notification_instance = None
          if user == team.creator:
               if not team_application.accepted:
                    try:
                         # set application notification as read (just in case)
                         if not team_application_notification.is_read:
                              team_application_notification.is_read = True
                              team_application_notification_instance = team_application_notification.save()
                         
                         # create team_application_declined notifcation for user
                         Notification.objects.create(
                              type="team_application_declined",
                              to_user = applicant,
                              related_id = team_application_notification.pk
                         )
                         serializer = TeamApplicationDetailSerializer(team_application)
                         return Response(serializer.data, status=status.HTTP_200_OK)
                    except:
                         if team_application_instance is not None:
                              team_application_instance.delete()
                         if team_application_notification_instance is not None:
                              team_application_notification_instance.delete()
                         Response({"message": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
               return Response({"message": "this team application is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"message": "user is not the team's creator"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class EnterTeamAPIView(APIView):
     def post(self, request):
          data = request.data
          
          team = get_object_or_404(Team, pk=data["team_id"])
          user = get_object_or_404(User, name=data["user"])
          background = data["background"]
          team_application = get_object_or_404(TeamApplication, team=team, applicant=user)
          position = team_application.position
          
          if user not in team.members.all():
               if team_application.accepted:
                    # set last notification as read (just in case)
                    acceptance_notification = get_object_or_404(Notification, type="team_application_accepted", related_id=team_application.pk)
                    if not acceptance_notification.is_read:
                         acceptance_notification.is_read = True
                         acceptance_notification.save()
                    
                    # reduce position cnt in TeamPosition
                    team_position = get_object_or_404(TeamPositions, team=team, position=position)
                    team_position.cnt -= 1
                    if team_position.cnt == 0:
                         team_position.delete()
                    else:
                         team_position.save()
                         
                    # create member to team
                    new_member = TeamMembers.objects.create(
                         team=team,
                         user=user,
                         position=position,
                         background=background
                    )
                    
                    return Response({"message": "user successfully entered team"}, status=status.HTTP_200_OK)
               return Response({"message": "team application is not accepted"}, status=status.HTTP_409_CONFLICT) 
          return Response({"message": "user is already team member"}, status=status.HTTP_409_CONFLICT)