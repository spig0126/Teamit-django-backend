from rest_framework import permissions

from .models import *
from team.models import TeamPermission

class IsPrivateChatParticipant(permissions.BasePermission):
     message = "permission denied because user is not participant"
     
     def has_permission(self, request, view):
          participants = view.chatroom.participants.all()
          return request.user in participants

class IsInquiryChatParticipant(permissions.BasePermission):
     message = "permission denied because user is not participant"
     
     def has_permission(self, request, view):
          responder = TeamPermission.objects.get(team=view.chatroom.team).responder
          inquirer = view.chatroom.inquirer
          
          return request.user in (responder, inquirer)

class IsTeamChatParticipant(permissions.BasePermission):
     message = "permission denied because user is not participant"
     
     def has_permission(self, request, view):
          participants = view.chatroom.participants.all()
          return request.user in participants

