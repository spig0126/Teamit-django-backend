from rest_framework import generics, status
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import *
from .serializers import *



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
          return PrivateChatRoom.objects.filter(participants=self.request.user)

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
