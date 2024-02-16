from rest_framework import generics, status
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from rest_framework.decorators import permission_classes
from django.db import transaction, IntegrityError

from .models import *
from .serializers import *
from .permissions import *
from team.models import TeamPermission
from team.utils import get_team_by_pk
from team.permissions import IsTeamMemberPermission
from team.serializers import TeamMemberDetailSerializer


class PrivateChatRoomDetailAPIView(CreateModelMixin, ListModelMixin, generics.GenericAPIView):
     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.request.user
          return context
     
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return PrivateChatRoomDeatilSerializer
          elif self.request.method == 'POST':
               return PrivateChatRoomCreateSerializer
     
     def get_queryset(self):
          blocked_users = self.request.user.blocked_users.values('pk')
          return PrivateChatRoom.objects.filter(participants=self.request.user).exclude(participants__in=blocked_users)

     def post(self, request, *args, **kwargs):
          # check if user is in list of paritcipants
          participants = request.data.get('participants', [])
          if request.user.name not in participants:
               return Response({"detail": "user can't create private chat room that one's not a part of"}, status=status.HTTP_403_FORBIDDEN)
          
          # check if there is already private chat room 
          if PrivateChatRoom.objects.filter(participants__name=participants[0]).filter(participants__name=participants[1]).exists():
               return Response({"detail": "private chat room already exists"}, status=status.HTTP_409_CONFLICT)
          
          return self.create(request, *args, **kwargs)

     def get(self, request, *args, **kwargs):
          return self.list(request, *args, **kwargs)


class PrivateChatRoomNameRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
     serializer_class = PrivateChatRoomNameSerializer

     def get_object(self):
          chatroom_pk = self.kwargs.get('pk', '')
          # 채팅 참여자 아니면 어차피 404 뜸
          return get_object_or_404(PrivateChatParticipant, user=self.request.user, chatroom__pk=chatroom_pk)

#######################################################
# inquiry chats

class InquiryChatRoomDetailAPIView(CreateModelMixin, ListModelMixin, generics.GenericAPIView):
     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.request.user
          return context
     
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return InquiryChatRoomDetailSerializer
          elif self.request.method == 'POST':
               return InquiryChatRoomCreateSerializer
     
     def get_queryset(self):
          responder_teams = TeamPermission.objects.filter(responder = self.request.user).values('team')
          responder_rooms = InquiryChatRoom.objects.filter(team__in=responder_teams)
          inquirer_rooms = InquiryChatRoom.objects.filter(inquirer=self.request.user)
          
          type = self.request.query_params.get('type', '')
          if type == 'responder':
               return responder_rooms
          elif type == 'inquirer':
               return inquirer_rooms
          else:
               all_rooms = responder_rooms.union(inquirer_rooms)
               return all_rooms.order_by('-updated_at')

     def post(self, request, *args, **kwargs):
          inquirer = request.data.get('inquirer', '')
          team = request.data.get('team', '')
          
          if request.user.name != inquirer:
               return Response({"detail": "user can't create inquiry chat room whose inquirer isn't the user"}, status=status.HTTP_403_FORBIDDEN) 
          if TeamMembers.objects.filter(team__pk=team, user=request.user).exists():
               return Response({"detail": "user can't inquiry team one's already member of"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY) 
          if InquiryChatRoom.objects.filter(inquirer=request.user, team__pk=team).exists():
               return Response({"detail": "inquiry chat room already exists"}, status=status.HTTP_409_CONFLICT)
          
          return self.create(request, *args, **kwargs)
     
     def get(self, request, *args, **kwargs):
          return self.list(request, *args, **kwargs)

@permission_classes([IsInquiryChatParticipant])
class CheckUserIsInquirerAPIView(generics.RetrieveAPIView):
     queryset = InquiryChatRoom.objects.all()
     
     def initial(self, request, *args, **kwargs):
          self.chatroom = self.get_object()
          super().initial(request, *args, **kwargs)
     
     def get(self, request, *args, **kwargs):
          user_is_inquirer = False
          if self.chatroom.inquirer == request.user:
               user_is_inquirer = True
          return Response({'user_is_inquirer': user_is_inquirer}, status=status.HTTP_200_OK) 
     
#######################################################
# team chats
# 채팅방 참여자인 경우 모두 가능하게
# 팀원 나갔을 경우 메시지 못 보내기
@permission_classes([IsTeamMemberPermission])
class TeamChatRoomDetailAPIView(CreateModelMixin, ListModelMixin, generics.GenericAPIView):
     def initial(self, request, *args, **kwargs):
          self.team_pk = self.kwargs.get('team_pk')
          self.team = get_team_by_pk(self.team_pk)
          super().initial(request, *args, **kwargs)

     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.request.user
          context['team'] = get_team_by_pk(self.team_pk)
          context['team_pk'] = self.team_pk
          return context
     
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return TeamChatRoomDetailSerializer
          elif self.request.method == 'POST':
               return TeamChatRoomCreateSerializer
     
     def get_queryset(self):
          return TeamChatRoom.objects.filter(team=self.team, participants=self.request.user)

     @transaction.atomic
     def post(self, request, *args, **kwargs):
          request.data['team'] = self.team.pk
          return self.create(request, *args, **kwargs)
     
     def get(self, request, *args, **kwargs):
          return self.list(request, *args, **kwargs)
     
@permission_classes([IsTeamChatParticipant])
class TeamChatRoomParticipantDetailAPIView(DestroyModelMixin, ListModelMixin, generics.GenericAPIView):     
     def initial(self, request, *args, **kwargs):
          self.chatroom = TeamChatRoom.objects.get(pk=kwargs.get('chatroom_pk'))
          super().initial(request, *args, **kwargs)
               
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return TeamMemberDetailSerializer
          elif self.request.method == 'POST':
               return TeamChatParticipantCreateSerializer
     
     def get_object(self):
          return TeamChatParticipant.objects.get(chatroom=self.chatroom, user=self.request.user)
     
     def get_queryset(self):
          participants = (
               TeamChatParticipant.objects
               .filter(chatroom=self.chatroom, member__isnull=False)
               .select_related('member', 'user')
               .annotate(
                    user_is_this_user=Case(
                         When(user=self.request.user, then=Value(0)),
                         default=Value(1),
                         output_field=IntegerField(),
                    )
               )
               .order_by('user_is_this_user', 'user__name')
          )
          members = [participant.member for participant in participants]
          return members
     
     def get(self, request, *args, **kwargs):
          return self.list(request, *args, **kwargs)
     
     def delete(self, request, *args, **kwargs):
          return self.destroy(request, *args, **kwargs)
          
     def post(self, request, *args, **kwargs):
          member_pks = request.data.get('members')
          serializer_class = self.get_serializer_class()
          team_members = TeamMembers.objects.filter(team=self.chatroom.team)
          members = TeamMembers.objects.filter(pk__in=member_pks)

          try:
               for member in members:
                    if member not in team_members:
                         raise serializers.ValidationError(
                              f"Some are not members of this team"
                         )
                    serializer = serializer_class(data={'chatroom': self.chatroom.pk, 'user': member.user.pk, 'member': member.pk})
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
               return Response(status=status.HTTP_201_CREATED)
          except IntegrityError as e:
               return Response({'detail': 'user is already chatroom participant'}, status=status.HTTP_409_CONFLICT)

@permission_classes([IsTeamChatParticipant])
class TeamChatRoomNonParticipantListAPIView(generics.ListAPIView):
     serializer_class = TeamMemberDetailSerializer
     
     def initial(self, request, *args, **kwargs):
          self.chatroom = TeamChatRoom.objects.get(pk=kwargs.get('chatroom_pk'))
          super().initial(request, *args, **kwargs)
     
     def get_queryset(self):
          participants = TeamChatParticipant.objects.filter(chatroom=self.chatroom, member__isnull=False).values_list('member', flat=True)
          non_participants = TeamMembers.objects.filter(team=self.chatroom.team).exclude(id__in=participants)
          return non_participants