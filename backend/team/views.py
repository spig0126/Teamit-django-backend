from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response

from .models import *
from .serializers import *
from notification.models import *
# from sys import path
# path.append('..')
# from backend.user.constants import UNAVAILABLE_NAMES

# Create views
class TeamCreateAPIView(generics.CreateAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamCreateUpdateSerializer
     
# detail views
class TeamDetailAPIView(generics.RetrieveAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamDetailSerializer

# update views
class TeamUpdateAPIView(generics.UpdateAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamCreateUpdateSerializer

     def update(self, request, *args, **kwargs):
          instance = self.get_object()
          serializer = self.get_serializer(instance, data=request.data, partial=True)
          if serializer.is_valid(raise_exception=True):
               self.perform_update(serializer)
               instance = self.get_object()
               response_serializer = TeamDetailSerializer(instance)
               return Response(response_serializer.data, status=status.HTTP_200_OK)
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

# delete views
class TeamDestroyAPIView(APIView):
     def post(self, request, *args, **kwargs):
          user = get_object_or_404(User, name=request.data['user'])
          team = get_object_or_404(Team, pk=request.data['team_pk'])

          if user == team.creator:
               team.delete()
               return Response({"message": "Team has successfully been destroyed"}, status=status.HTTP_204_NO_CONTENT)


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
                    return Response({"error": "this team application already exists"}, status=status.HTTP_409_CONFLICT)   
               return Response({"error": "user is already a member of team"}, status=status.HTTP_400_BAD_REQUEST) 
          return Response({"error": "the position is already taken or doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
     
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
                         Response({"error": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
               return Response({"error": "this team application is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "user is not the team's creator"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

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
                         Response({"error": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
               return Response({"error": "this team application is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "user is not the team's creator"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

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
               return Response({"error": "team application is not accepted"}, status=status.HTTP_409_CONFLICT) 
          return Response({"error": "user is already team member"}, status=status.HTTP_409_CONFLICT)

class LeaveTeamAPIVIew(APIView):
     def post(self, request):
          data = request.data
          
          team = get_object_or_404(Team, pk=data['team_pk'])
          user = get_object_or_404(User, name=data['user'])
          team_members = team.members.all()
          if user in team_members:
               TeamMembers.objects.get(user=user, team=team).delete()
               return Response({'message': 'user successfully left the team'}, status=status.HTTP_204_NO_CONTENT)
          return Response({'error': 'user is not a member of the team'}, status=status.HTTP_404_NOT_FOUND)

class DropTeamMemberAPIVIew(APIView):
     def post(self, request):
          data = request.data
          
          team = get_object_or_404(Team, pk=data['team_pk'])
          drop_member = get_object_or_404(User, name=data['drop_member'])
          user = get_object_or_404(User, name=data['user'])
          team_members = team.members.all()
          if user == team.creator:
               if team.creator != drop_member:
                    if drop_member in team_members:
                         TeamMembers.objects.get(user=drop_member, team=team).delete()
                         return Response({'message': 'user successfully left the team'}, status=status.HTTP_204_NO_CONTENT)
                    return Response({'error': 'drop_member is not a member of the team'}, status=status.HTTP_404_NOT_FOUND)
               return Response({'error': 'you cannot drop the tem creator. if you want to do this, please delete the team itself.'}, status=status.HTTP_409_CONFLICT)
          return Response({'error': "user is not the team creator"}, status=status.HTTP_403_FORBIDDEN)
     