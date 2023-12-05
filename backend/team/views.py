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

class TeamSimpleDetailAPIView(generics.RetrieveAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamSimpleDetailSerializer
     


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
                    if not TeamApplication.objects.filter(applicant=applicant, team=team, accepted=None).exists():
                         team_application  = TeamApplication.objects.create(    # TeamNotification 자동적으로 생성됨
                              team = team,
                              applicant = applicant,
                              position = position
                         )
                         serializer = TeamApplicationDetailSerializer(team_application)
                         return Response(serializer.data, status=status.HTTP_200_OK)
                    return Response({"error": "this team application already exists"}, status=status.HTTP_208_ALREADY_REPORTED)   
               return Response({"error": "user is already a member of team"}, status=status.HTTP_409_CONFLICT) 
          return Response({"error": "the position is already taken or doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
     
class AcceptTeamApplicationAPIView(APIView):
     def post(self, request):
          data = request.data
          
          team_application = get_object_or_404(TeamApplication, pk=data['team_application_id'], accepted=None)
          user = get_object_or_404(User, name=data['user'])
          team_application_notification = get_object_or_404(TeamNotification, related=team_application, type="team_application")
          team = team_application.team
          applicant = team_application.applicant
          
          if user == team.creator:
               if team_application.accepted is None:
                    try:
                         team_application.accepted = True
                         
                         # set application notification type to show it's processed
                         team_application_notification.type = "team_application_accept"
                         
                         # set application notification as read (just in case)
                         if not team_application_notification.is_read:
                              team_application_notification.is_read = True
                         
                         # create team_application_accepted notifcation for user
                         Notification.objects.create(
                              type="team_application_accepted",
                              to_user = applicant,
                              related_id = team_application.pk
                         )
                         serializer = TeamApplicationDetailSerializer(team_application)
                    except:
                         Response({"error": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                         team_application.save()
                         team_application_notification.save()
                         return Response(serializer.data, status=status.HTTP_200_OK)
               return Response({"error": "this team application is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "user is not the team's creator"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class DeclineTeamApplicationAPIView(APIView):
     def post(self, request):
          data = request.data
          
          team_application = get_object_or_404(TeamApplication, pk=data['team_application_id'], accepted=None)
          user = get_object_or_404(User, name=request.data['user'])
          team_application_notification = get_object_or_404(TeamNotification, related=team_application, type="team_application")
          team = team_application.team
          applicant = team_application.applicant

          if user == team.creator:
               if team_application.accepted is None:
                    # set team application accepted to false
                    team_application.accepted = False
                    team_application.save()
                    
                    # delete team notification
                    team_application_notification.delete()

                    # create team_application_declined notifcation for user
                    Notification.objects.create(
                         type="team_application_declined",
                         to_user = applicant,
                         related_id = team_application.pk
                    )
                    serializer = TeamApplicationDetailSerializer(team_application)
                    return Response(serializer.data, status=status.HTTP_200_OK)
               return Response({"error": "this team application is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "user is not the team's creator"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class UserDeclineTeamInvitationAPIView(APIView):
     def post(self, request):
          data = request.data
          
          user = get_object_or_404(User, name=request.data['user'])
          notification = get_object_or_404(Notification, pk=data['notification_id'], type="team_application_accepted")
          
          team_application = get_object_or_404(TeamApplication, pk=notification.related_id)
          
          if user == team_application.applicant:
               if team_application.accepted:
                    # delete notification of team_application_accepted
                    notification.delete()
                    
                    # send TeamNotification to team that invitation has been declined
                    TeamNotification.objects.create(
                         type="team_invitation_declined",
                         related=team_application,
                         to_team = team_application.team
                    )
                    return Response({"message": "team invitation successfully declined"}, status=status.HTTP_200_OK)
               return Response({"error": "user can't decline invitation when application wasn't accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "user is not the invitation's recipient"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                    
class UserAcceptTeamInvitationAPIView(APIView):
     def post(self, request):
          data = request.data
          
          # request data
          notification = get_object_or_404(Notification, pk=data['notification_id'], type="team_application_accepted")
          user = get_object_or_404(User, name=request.data['user'])
          background = data['background']
          
          # needed data
          team_application = get_object_or_404(TeamApplication, pk=notification.related_id)
          team = team_application.team
          position = team_application.position
          team_position = get_object_or_404(TeamPositions, team=team, position=position)

          if user not in team.members.all():
               if team_application.accepted:
                    # change notification type to "team_invitation_accept"
                    notification.type = "team_invitation_accept"
                    notification.is_read = True
                    notification.save()
                    
                    # update team's recruiting positions
                    team_position.cnt -= 1
                    if team_position.cnt == 0:
                         team_position.delete()
                    else:
                         team_position.save()
                    
                    # add user to team member
                    new_member = TeamMembers.objects.create(
                         team=team,
                         user=user,
                         position=position,
                         background=background
                    )
                    
                    # alert team that invitation was accepted
                    TeamNotification.objects.create(
                         type="team_invitation_accepted",
                         related=team_application,
                         to_team=team
                    )
                    return Response({"message": "user successfully entered team"}, status=status.HTTP_200_OK)
               return Response({"error": "team application has not been accepted yet or has been declined"}, status=status.HTTP_409_CONFLICT)  
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
     