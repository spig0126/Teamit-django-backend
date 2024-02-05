from rest_framework import generics, status
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import *
from .serializers import *
from team.models import TeamPermission


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

class PrivateChatRoomNameUpdateAPIView(generics.UpdateAPIView):
     serializer_class = PrivateChatParticipantDetailSerializer

     def get_serializer_context(self):
          context = super().get_serializer_context()
          context['user'] = self.request.user
          context['request'] = self.request
          return context
     
     def get_object(self):
          chatroom_pk = self.kwargs.get('pk', '')
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
