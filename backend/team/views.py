from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from django.db.models import F
from datetime import date
from rest_framework.decorators import permission_classes
from django.db import transaction


from .models import *
from .serializers import *
from .index import TeamIndex
from . import client
from .permissions import *
from .exceptions import *
from .utils import *
from notification.models import *
from position.models import Position
from fcm_notification.utils import send_fcm_to_user, send_fcm_to_team
from home.utilities import delete_s3_folder

class TeamListCreateAPIView(generics.ListCreateAPIView):  # list my teams
     def initial(self, request, *args, **kwargs):
          self.user = request.user
          self.activity = request.query_params.get('activity', None)
          super().initial(request, *args, **kwargs)

     def get_queryset(self):
          if self.activity is not None: # list all teams filtered by activity
               teams = Team.objects
               if self.activity != '1':   
                    teams = teams.filter(activity=self.activity)
               teams = (teams
                         .exclude(pk__in=self.user.blocked_teams.all().values_list('pk', flat=True))
                         .exclude(members=self.user)
                         .order_by('?')
               )
               
                         
               # values_list = [
               #      'id',
               #      'name',
               #      'image',
               #      # 'activity',
               #      # 'interest',
               #      'keywords', 
               #      # 'positions'
               # ]
               # teams = teams.values(
               #      'id',
               #      'name',
               #      'image',
               #      # 'activity',
               #      # 'interest',
               #      'keywords', 
               #      # 'positions')
               # ).prefetch_related(
                    
               # )
          else:     # list my teams
               teams = Team.objects.filter(members=self.user)
          return teams

     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.user
          return context

     def get_serializer_class(self):
          if self.request.method == 'POST':  # create team
               return TeamCreateUpdateSerializer
          elif self.request.method == 'GET':
               if self.activity is None: # list my teams
                    return MyTeamSimpleDetailSerializer
               else:       # list all teams filtered by activity
                    return TeamSimpleDetailSerializer

class RecommendedTeamListAPIView(generics.ListAPIView):
     serializer_class = TeamSimpleDetailSerializer
     
     def get_queryset(self):
          teams = Team.objects.all()
          user = self.request.user
          today_date = date.today().isoformat()
          
          my_team_ids = user.teams.values_list('pk', flat=True)
          blocked_team_ids = user.blocked_teams.values_list('pk', flat=True)

          # exclude user's teams, blocked teams, and non-active teams
          teams = teams.exclude(pk__in=my_team_ids).exclude(pk__in=blocked_team_ids).exclude(active_enddate__lt=today_date)

          # filter recruit_enddate and order teams randomly
          teams = teams.filter(recruit_enddate__gte=today_date).order_by('?')
          teams = [team for team in teams if len(team.positions.all()) > 0]
               
          return teams[:50]
     
@permission_classes([IsTeamCreatorPermission])
class TeamDetailAPIView(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericAPIView):
     queryset = Team.objects.all()
     lookup_url_kwarg = 'team_pk'
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
          
     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.request.user
          return context

     def get_serializer_class(self):
          if self.request.method == 'GET':
               return TeamDetailSerializer
          elif self.request.method == 'PATCH':
               return TeamCreateUpdateSerializer

     def get(self, request, *args, **kwargs):
          return self.retrieve(request, *args, **kwargs)

     def patch(self, request, *args, **kwargs):
          return self.partial_update(request, *args, **kwargs)

     @transaction.atomic
     def delete(self, request, *args, **kwargs):
          delete_s3_folder(f'teams/{self.team.pk}/')
          return self.destroy(request, *args, **kwargs)

@permission_classes([IsTeamMemberPermission])
class MyTeamRoomDetailAPIView(generics.RetrieveAPIView):
     queryset = Team.objects.all()
     serializer_class = MyTeamRoomDetailSerializer
     lookup_url_kwarg = 'team_pk'
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
          
     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.request.user
          return context

@permission_classes([IsTeamMemberPermission])
class HasUnreadTeamNotifications(APIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
          
     def get(self, request, *args, **kwargs):
          member = TeamMembers.objects.get(team=self.team, user=request.user)
          data = {"has_new_team_notifications": False}
          if member.noti_unread_cnt:
               data['has_new_team_notifications'] = True
          return Response(data, status=status.HTTP_200_OK)
          

@permission_classes([IsTeamCreatorPermission]) 
class TeamBeforeUpdateDetailAPIView(generics.RetrieveAPIView):
     queryset = Team.objects.all()
     serializer_class = TeamBeforeUpdateDetailSerializer
     lookup_url_kwarg = 'team_pk'    
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)

class TeamMemberListAPIView(generics.ListAPIView):
     serializer_class = TeamMemberDetailSerializer
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
     
     def get_queryset(self):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          return TeamMembers.objects.filter(team=team)
     
class TeamPositionListAPIView(generics.ListAPIView):
     serializer_class = TeamPositionDetailSerializer
     
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)
     
     def get_queryset(self):
          team = get_object_or_404(Team, pk=self.kwargs.get('pk'))
          return TeamPositions.objects.filter(team=team)

# Team member views
class TeamMemberListCreateAPIView(generics.ListCreateAPIView):
     serializer_class = TeamMemberDetailSerializer
          
     def initial(self, request, *args, **kwargs):
          if self.request.method == 'GET':
               request.skip_authentication = True
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
     
     def get_queryset(self):
          return TeamMembers.objects.filter(team=self.team)
     
     @transaction.atomic
     def create(self, request, *args, **kwargs):
          notification = get_object_or_404(Notification, pk=request.data['notification_id'], type="team_application_accepted")
          background = request.data['background']
          
          team_application = get_object_or_404(TeamApplication, pk=notification.related_id)
          team = team_application.team
          applicant = team_application.applicant
          position = team_application.position
          team_position = get_object_or_404(TeamPositions, team=team, position=position)
          
          if applicant in team.members.all():
               return Response({"detail": "user is already team member"}, status=status.HTTP_409_CONFLICT)
          if team.pk != self.team.pk:
               return Response({"detail": "team has nothing to do with this application"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
          if applicant != request.user:
               return Response({"detail": "user is not applicant"}, status=status.HTTP_400_BAD_REQUEST)
          
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
          
          # alert team that invitation was accepted
          TeamNotification.objects.create(
               type="team_invitation_accepted",
               related=team_application,
               to_team=team
          )
          
          # send fcm to team to original members
          title = f'{team.name} 지원'
          body = f'{applicant.name} 님이 {position.name} 포지션을 수락하셨습니다.'
          data = {
               "page": "team_notification",
               "team_pk": str(team.pk),
               "team_name": team.name

          }
          send_fcm_to_team(team, title, body, data)
          
          # add user to team member
          TeamMembers.objects.create(
               team=team,
               user=applicant,
               position=position,
               background=background
          )

          serializer = TeamApplicationDetailSerializer(team_application)
          return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMemberDeclineAPIView(APIView):
     @transaction.atomic
     def put(self, request, *args, **kwargs):
          notification = get_object_or_404(Notification, pk=request.data['notification_id'], type="team_application_accepted")
          team_application = get_object_or_404(TeamApplication, pk=notification.related_id)
          team = team_application.team
          
          if request.user != team_application.applicant:
               raise PermissionDenied("user not allowed to decline member invitation") 
          
          # delete notification of team_application_accepted
          notification.delete()
          
          # send TeamNotification to team that invitation has been declined
          TeamNotification.objects.create(
               type="team_invitation_declined",
               related=team_application,
               to_team = team_application.team
          )
          
          # send fcm to team
          title = f'{team.name} 지원'
          body = f'{team_application.applicant.name} 님이 {team_application.position.name} 포지션을 거절하셨습니다.'
          data = {
               "page": "team_notification",
               "team_pk": str(team.pk),
               "team_name": team.name

          }
          send_fcm_to_team(team, title, body, data)
          
          return Response({"message": "team invitation successfully declined"}, status=status.HTTP_200_OK)
     
class TeamMemberDestroyAPIView(generics.DestroyAPIView):
     queryset = TeamMembers.objects.all()
     
     @transaction.atomic
     def delete(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          member_pk = kwargs.get('member_pk')
          
          team = get_object_or_404(Team, pk=team_pk)
          member = get_object_or_404(TeamMembers, pk=member_pk)
          user = request.user
          
          if user != member.user:
               raise PermissionDenied("user is not this member")
          if user == team.creator:
               return Response({'detail': 'creator cant leave team. if creator wants to leave, please delete the team itself'}, status=status.HTTP_409_CONFLICT)
          if user in team.members.all():
               member.delete()
               related_team_application_pks = TeamApplication.objects.filter(team=team, applicant=member.user).values_list('pk', flat=True)
               Notification.objects.filter(type__startswith='t', related_id__in=related_team_application_pks).delete()
               TeamApplication.objects.filter(pk__in=related_team_application_pks).delete()
               return Response(status=status.HTTP_204_NO_CONTENT)
          return Response({'detail': "user is this team's member"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY) 

@permission_classes([IsTeamCreatorPermission])       
class TeamMemberDropAPIView(generics.DestroyAPIView):
     queryset = TeamMembers.objects.all()
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
          
     @transaction.atomic
     def delete(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          member_pk =kwargs.get('member_pk')
          
          team = get_object_or_404(Team, pk=team_pk)
          member = get_object_or_404(TeamMembers, pk=member_pk)
          user = request.user

          if member.user == team.creator:
               return Response({'detail': 'you cannot drop the team creator. if you want to do this, please delete the team itself.'}, status=status.HTTP_409_CONFLICT)
          if member.user in team.members.all():
               # delete notifications and team applications related to member
               related_team_application_pks = TeamApplication.objects.filter(team=team, applicant=member.user).values_list('pk', flat=True)
               Notification.objects.filter(type__startswith='t', related_id__in=related_team_application_pks).delete()
               TeamApplication.objects.filter(pk__in=related_team_application_pks).delete()
               
               # delete user from member
               member.delete()
               
               return Response(status=status.HTTP_204_NO_CONTENT)
          return Response({'detail': "member is not this team's member"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY) 

class TeamMemberUpdateAPIView(generics.UpdateAPIView):
     serializer_class = MyTeamMemberDetailSerializer
     lookup_field = 'member_pk'
     
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.member_pk = self.kwargs.get('member_pk', None)
          super().initial(request, *args, **kwargs)
          
     def get_object(self):
          return get_object_or_404(TeamMembers, pk=self.kwargs.get('member_pk'))
     
     def get_queryset(self):
          teammember_pk = self.kwargs.get('member_pk')
          return TeamMembers.objects.filter(pk=teammember_pk)
     
     def get_permissions(self):
          field = self.request.query_params.get('field', None)
          if field == 'position':
               return [IsTeamCreatorPermission()]
          elif field == 'name':
               return [IsTeamMemberPermission(), IsThisTeamMemberPermission()]
          return super().get_permissions()

     
# team application related views
class TeamApplicationListCreateAPIView(generics.ListCreateAPIView):
     serializer_class = TeamApplicationDetailSerializer
          
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)

     def get_permissions(self):
          if self.request.method == 'GET':
               permission_classes = [IsTeamMemberPermission]
          elif self.request.method == 'POST':
               permission_classes = [IsNotTeamMemberPermission]
          return [permission() for permission in permission_classes]
     
     def get_queryset(self):
          return TeamApplication.objects.filter(team=self.team)
     
     @transaction.atomic
     def create(self, request, *args, **kwargs):
          team = self.team
          applicant = request.user
          position = get_object_or_404(Position, name=request.data["position"])
          
          if team.positions.all().filter(name=position.name).exists():
               if not TeamApplication.objects.filter(applicant=applicant, team=team, accepted=None).exists():
                    team_application  = TeamApplication.objects.create(    # TeamNotification 자동적으로 생성됨
                         team = team,
                         applicant = applicant,
                         position = position
                    )
                    serializer = TeamApplicationDetailSerializer(team_application)
                    
                    # send fcm to team
                    title = f'{team.name} 지원'
                    body = f'{applicant.name} 님이 {position.name} 포지션으로 지원하였습니다.'
                    data = {
                         "page": "team_notification",
                         "team_pk": str(team.pk),
                         "team_name": team.name    
                    }
                    send_fcm_to_team(team, title, body, data)
          
                    return Response(serializer.data, status=status.HTTP_200_OK)
               return Response({"detail": "this team application already exists"}, status=status.HTTP_208_ALREADY_REPORTED)   
          return Response({"detail": "the position is already taken or doesn't exist"}, status=status.HTTP_404_NOT_FOUND)

@permission_classes([IsTeamCreatorPermission])
class TeamApplicationAcceptAPIView(APIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
          
     @transaction.atomic
     def put(self, request, *args, **kwargs):
          team_pk = int(kwargs.get('team_pk'))
          application_pk = int(kwargs.get('application_pk'))
          
          team_application = get_object_or_404(TeamApplication, pk=application_pk)
          team_application_notification = get_object_or_404(TeamNotification, related=team_application, type="team_application")
          team = team_application.team
          applicant = team_application.applicant
          if team_pk == team.pk:
               try:
                    # update team application accepted status
                    team_application.accepted = True
                    
                    # set application notification type to show it's processed
                    team_application_notification.type = "team_application_accept"
                    
                    # create team_application_accepted notifcation for user
                    notification = Notification.objects.create(
                         type="team_application_accepted",
                         to_user = applicant,
                         related_id = team_application.pk
                    )
                    
                    # send fcm notification
                    title = '지원 결과 도착'
                    body = '지원 결과를 확인하세요!'
                    data = {
                         "page": "user_notification"
                    }
                    send_fcm_to_user(applicant, title, body, data)
                    
                    serializer = TeamApplicationDetailSerializer(team_application)
               except:
                    return Response({"error": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
               else:
                    team_application.save()
                    team_application_notification.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
          return Response({"detail": "team didn't receive this application"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

@permission_classes([IsTeamCreatorPermission])
class TeamApplicationDeclineAPIView(APIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)

     @transaction.atomic
     def put(self, request, *args, **kwargs):
          team_pk = kwargs.get('team_pk')
          application_pk = kwargs.get('application_pk')
          
          team_application = get_object_or_404(TeamApplication, pk=application_pk, accepted=None)
          team_application_notification = get_object_or_404(TeamNotification, related=team_application, type="team_application")
          team = team_application.team
          applicant = team_application.applicant

          if team_pk == team.pk:
               # set team application accepted to false
               team_application.accepted = False
               team_application.save()
               
               # delete team notification
               team_application_notification.delete()

               # create team_application_declined notifcation for user
               notification = Notification.objects.create(
                    type="team_application_declined",
                    to_user = applicant,
                    related_id = team_application.pk
               )
               
               # send fcm notification
               title = '지원 결과 도착'
               body = '지원 결과를 확인하세요!'
               data = {
                    "page": "user_notification"
               }
               send_fcm_to_user(applicant, title, body, data)
                    
               serializer = TeamApplicationDetailSerializer(team_application)
               return Response(serializer.data, status=status.HTTP_200_OK)
          return Response({"detail": "team didn't receive this application"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


# team likes related views
class UserTeamLikesListAPIView(APIView):
     def get(self, request, *args, **kwargs):
          team_likes = [obj.team for obj in TeamLike.objects.filter(user=request.user)]
          context = {'user': request.user}
          serializer = TeamLikesListSerializer(team_likes, context=context)
          return Response(serializer.data, status=status.HTTP_200_OK)
     
class TeamLikeUnlikeAPIView(APIView):
     @transaction.atomic
     def put(self, request, *args, **kwargs):
          team = get_object_or_404(Team, pk=self.kwargs.get('team_pk'))
          user = request.user
          try:
               team_like = TeamLike.objects.get(team=team, user=user)
               team_like.delete()
               return Response({"message": "team unliked"}, status=status.HTTP_204_NO_CONTENT)
          except:
               TeamLike.objects.create(team=team, user=user)
               return Response({"message": "team liked"}, status=status.HTTP_201_CREATED)


# block team related views
@permission_classes([IsNotTeamMemberPermission])
class BlockUnblockTeamAPIView(APIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          self.user = request.user
          super().initial(request, *args, **kwargs)
          
     def put(self, request, *args, **kwargs):
          if self.team in self.user.blocked_teams.all():
               self.user.blocked_teams.remove(self.team)
               return Response({"message": "team unblocked"}, status=status.HTTP_204_NO_CONTENT)
          else:
               self.user.blocked_teams.add(self.team)
               return Response({"message": "team blocked"}, status=status.HTTP_201_CREATED) 

class BlockedTeamListAPIView(generics.ListAPIView):
     serializer_class = TeamSimpleDetailSerializer

     def get_queryset(self):
          return self.request.user.blocked_teams.all()
     
# permission
@permission_classes([IsTeamCreatorPermission])   
class TeamPermissionUpdateAPIView(generics.UpdateAPIView):
     serializer_class = TeamPermissionDetailSerializer
     lookup_url_kwarg = 'team_pk'

     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
          
     def get_object(self):
          return TeamPermission.objects.get(team=self.team)
     
@permission_classes([IsTeamCreatorPermission])
class UpdateTeamCreatorAPIView(APIView):
     def initial(self, request, *args, **kwargs):
          self.team = get_team_by_pk(self.kwargs.get('team_pk'))
          super().initial(request, *args, **kwargs)
     
     def patch(self, request, *args, **kwargs):
          user = get_object_or_404(User, pk=kwargs.get('user_pk'))
          if not self.team.members.filter(pk=user.pk).exists():
               return Response({'detail': 'only team member can be team creator'}, status=status.HTTP_403_FORBIDDEN)
          self.team.creator = user
          self.team.save()
          return Response(status=status.HTTP_200_OK)
     
# search api
class TeamSearchAPIView(generics.ListAPIView):
     serializer_class = SearchedTeamDetailSerializer
               
     def get_queryset(self):
          # Retrieve the search query from the request
          query = self.request.query_params.get('q')
          blocked_team_pks = set(self.request.user.blocked_teams.all().values_list('pk', flat=True))

          if query:
               results = client.perform_search(query)
               pks = set([int(result['objectID']) for result in results['hits']])
               
               user = self.request.user

               # exclude user itself and blocked users
               pks = pks - blocked_team_pks
                           
               teams = Team.objects.filter(pk__in=pks)
          else:
               teams = Team.objects.exclude(pk__in=blocked_team_pks)
          return teams