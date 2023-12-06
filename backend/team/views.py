from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin

from .models import *
from .serializers import *
from notification.models import *
from position.models import Position
# CRUD views for Team
class TeamListCreateAPIView(generics.ListCreateAPIView):     
     def get_serializer_class(self):
          if self.request.method == 'POST':
               return TeamCreateUpdateSerializer
          elif self.request.method == 'GET':
               type = self.request.query_params.get('type')
               if type is None or type == 'detailed':
                    return TeamDetailSerializer
               elif type == 'simple':
                    return TeamSimpleDetailSerializer

     def get_queryset(self):
          activity = self.request.query_params.get('activity')
          if activity is not None:
               queryset = Team.objects.filter(activity=activity)
          else:
               queryset = Team.objects.all()
          return queryset
     
class TeamDetailAPIView(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):
     queryset = Team.objects.all()

     def get_serializer_class(self):
          serializer_class = TeamDetailSerializer

          if self.request.method == 'GET':
               type = self.request.query_params.get('type')
               if type is None or type == 'detailed':
                    return TeamDetailSerializer
               elif type == 'simple':
                    return TeamSimpleDetailSerializer
          elif self.request.method == 'PATCH':
               return TeamCreateUpdateSerializer
          return serializer_class

     def get(self, request, *args, **kwargs):
          return self.retrieve(request, *args, **kwargs)

     def patch(self, request, *args, **kwargs):
          user_pk = request.headers.get('UserID')
          user = get_object_or_404(User, pk=user_pk)
          team = self.get_object()
          if user != team.creator:
               raise PermissionDenied("user is not allowed to update this team")
          return self.partial_update(request, *args, **kwargs)

     def delete(self, request, *args, **kwargs):
          user_pk = request.headers.get('UserID')
          user = get_object_or_404(User, pk=user_pk)
          team = self.get_object()
          if user != team.creator:
               raise PermissionDenied("user is not allowed to delete this team")
          return self.destroy(request, *args, **kwargs)

class TeamMemberListAPIView(generics.ListAPIView):
     serializer_class = TeamMemberDetailSerializer
     
     def get_queryset(self):
          team = get_object_or_404(Team, pk=self.kwargs.get('pk'))
          return TeamMembers.objects.filter(team=team)
     
class TeamPositionListAPIView(generics.ListAPIView):
     serializer_class = TeamPositionDetailSerializer
     
     def get_queryset(self):
          team = get_object_or_404(Team, pk=self.kwargs.get('pk'))
          return TeamPositions.objects.filter(team=team)


# Team member views
class TeamMemberListCreateAPIView(generics.ListCreateAPIView):
     serializer_class = TeamMemberDetailSerializer
     
     def get_queryset(self):
          team_pk = self.kwargs.get('team_pk')
          team = get_object_or_404(Team, pk=team_pk)
          return TeamMembers.objects.filter(team=team)
     
     def create(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          user_pk = request.headers.get('UserID')
          notification = get_object_or_404(Notification, pk=request.data['notification_id'], type="team_application_accepted")
          background = request.data['background']
          
          user = get_object_or_404(User, pk=user_pk)
          team_application = get_object_or_404(TeamApplication, pk=notification.related_id)
          team = team_application.team
          position = team_application.position
          team_position = get_object_or_404(TeamPositions, team=team, position=position)
          
          if user != team_application.applicant:
               raise PermissionDenied("user not allowed to accpet member invitation")
          if team_pk != team.pk:
               return Response({"detail": "team has nothing to do with this application"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
          if user in team.members.all():
               return Response({"detail": "user is already team member"}, status=status.HTTP_409_CONFLICT)

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
          serializer = TeamApplicationDetailSerializer(team_application)
          return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMemberDeclineAPIView(APIView):
     def put(self, request, *args, **kwargs):
          notification = get_object_or_404(Notification, pk=request.data['notification_id'], type="team_application_accepted")
          team_application = get_object_or_404(TeamApplication, pk=notification.related_id)
          
          user = get_object_or_404(User, pk=request.headers.get('UserID'))
          print('hello')
          
          if user != team_application.applicant:
               raise PermissionDenied("user not allowed to decline member invitation") 
          
          # delete notification of team_application_accepted
          notification.delete()
          
          # send TeamNotification to team that invitation has been declined
          TeamNotification.objects.create(
               type="team_invitation_declined",
               related=team_application,
               to_team = team_application.team
          )
          return Response({"message": "team invitation successfully declined"}, status=status.HTTP_200_OK)
     
class TeamMemberDestroyAPIView(generics.DestroyAPIView):
     queryset = TeamMembers.objects.all()
     
     def delete(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          member_pk = kwargs.get('member_pk')
          user_pk = request.headers.get('UserID')
          
          team = get_object_or_404(Team, pk=team_pk)
          member = get_object_or_404(TeamMembers, pk=member_pk)
          user = get_object_or_404(User, pk=user_pk)
          
          if user != member.user:
               raise PermissionDenied("user is not this member")
          if user == team.creator:
               return Response({'detail': 'creator cant leave team. if creator wants to leave, please delete the team itself'}, status=status.HTTP_409_CONFLICT)
          if user in team.members.all():
               member.delete()
               return Response(status=status.HTTP_204_NO_CONTENT)
          return Response({'detail': "user is this team's member"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY) 
          
class TeamMemberDropAPIView(generics.DestroyAPIView):
     queryset = TeamMembers.objects.all()
     
     def delete(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          member_pk =kwargs.get('member_pk')
          user_pk = request.headers.get('UserID')
          
          team = get_object_or_404(Team, pk=team_pk)
          member = get_object_or_404(TeamMembers, pk=member_pk)
          user = get_object_or_404(User, pk=user_pk)
          
          if user != team.creator:
               raise PermissionDenied("user not allowed to drop this member")
          if member.user == team.creator:
               return Response({'detail': 'you cannot drop the team creator. if you want to do this, please delete the team itself.'}, status=status.HTTP_409_CONFLICT)
          print(team.members.all())
          if member.user in team.members.all():
               member.delete()
               return Response(status=status.HTTP_204_NO_CONTENT)
          return Response({'detail': "member is not this team's member"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY) 
     
     
# team application related views
class TeamApplicationListCreateAPIView(generics.ListCreateAPIView):
     serializer_class = TeamApplicationDetailSerializer
     
     def get_queryset(self):
          team_pk = self.kwargs.get('team_pk')
          user_pk = self.request.headers.get('UserID')
          
          team = get_object_or_404(Team, pk=team_pk)
          user = get_object_or_404(User, pk=user_pk)
          
          if user in team.members.all():
               return TeamApplication.objects.filter(team=team)
          raise PermissionDenied("user is not allowed to view this team's applications")
     
     def create(self, request, *args, **kwargs):
          team_pk = self.kwargs.get('team_pk')
          user_pk = self.request.headers.get('UserID')

          team = get_object_or_404(Team, pk=team_pk)
          applicant = get_object_or_404(User, pk=user_pk)
          position = get_object_or_404(Position, name=request.data["position"])
          
          if team.positions.all().filter(name=position.name).exists():
               if applicant not in team.members.all():
                    if not TeamApplication.objects.filter(applicant=applicant, team=team, accepted=None).exists():
                         team_application  = TeamApplication.objects.create(    # TeamNotification 자동적으로 생성됨
                              team = team,
                              applicant = applicant,
                              position = position
                         )
                         serializer = TeamApplicationDetailSerializer(team_application)
                         return Response(serializer.data, status=status.HTTP_200_OK)
                    return Response({"detail": "this team application already exists"}, status=status.HTTP_208_ALREADY_REPORTED)   
               return Response({"detail": "user is already a member of team"}, status=status.HTTP_409_CONFLICT) 
          return Response({"detail": "the position is already taken or doesn't exist"}, status=status.HTTP_404_NOT_FOUND)
     
class TeamApplicationAcceptAPIView(APIView):
     def put(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          application_pk = kwargs.get('application_pk')
          user_pk = request.headers.get('UserID')
          
          team_application = get_object_or_404(TeamApplication, pk=application_pk)
          user = get_object_or_404(User, pk=user_pk)
          team_application_notification = get_object_or_404(TeamNotification, related=team_application, type="team_application")
          team = team_application.team
          applicant = team_application.applicant
          
          if user != team.creator:
               raise PermissionDenied("user is not allowed to accpet this team application")
          if team_pk == team.pk:
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
          return Response({"detail": "team didn't receive this application"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class TeamApplicationDeclineAPIView(APIView):
     def put(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          application_pk = kwargs.get('application_pk')
          user_pk = request.headers.get('UserID')
          
          team_application = get_object_or_404(TeamApplication, pk=application_pk, accepted=None)
          user = get_object_or_404(User, pk=user_pk)
          team_application_notification = get_object_or_404(TeamNotification, related=team_application, type="team_application")
          team = team_application.team
          applicant = team_application.applicant
          
          if user != team.creator:
               raise PermissionDenied("user is not allowed to accpet this team application")
          if team_pk == team.pk:
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
          return Response({"detail": "team didn't receive this application"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


# team likes related views
class UserTeamLikesListAPIView(APIView):
     def get(self, request, *args, **kwargs):
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          team_likes = [obj.team for obj in TeamLike.objects.filter(user=user)]
          serializer = TeamLikesListSerializer(team_likes)
          return Response(serializer.data, status=status.HTTP_200_OK)
     
class TeamLikeUnlikeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          try:
               team_like = TeamLike.objects.get(team=team, user=user)
               team_like.delete()
               return Response({"message": "team unliked"}, status=status.HTTP_204_NO_CONTENT)
          except:
               TeamLike.objects.create(team=team, user=user)
               return Response({"message": "team liked"}, status=status.HTTP_201_CREATED)
