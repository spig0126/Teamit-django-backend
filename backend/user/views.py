from django.shortcuts import get_object_or_404
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from .models import *
from .serializers import *
from activity.models import Activity
from region.models import Province, City
from notification.models import Notification
from sys import path
path.append('..')
from constants import UNAVAILABLE_NAMES

class UserWithProfileCreateAPIView(generics.CreateAPIView):
     queryset = UserProfile.objects.all()
     serializer_class = UserProfileCreateSerializer
     
     def create(self, request, *args, **kwargs):
          serializer = self.get_serializer(data=request.data)
          if serializer.is_valid(raise_exception=True):
               serializer.save()
               return Response({"message": "User & UserProfile succesfully created"}, status=status.HTTP_200_OK)
               
class UserDetailAPIView(generics.RetrieveAPIView):
     queryset = User.objects.all()
     serializer_class = UserDetailSerializer
     lookup_field = 'name'
     
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()


class CheckUserNameAvailability(APIView):
     def get(self, request):
          name = request.GET.get('name')
          
          try:
               user = User.objects.get(name=name)
               return Response({"error": "name '{}' is unavailable".format(name)}, status=status.HTTP_400_BAD_REQUEST)
          except:
               if name not in UNAVAILABLE_NAMES:
                    return Response({"message": "name '{}' is available".format(name)}, status=status.HTTP_200_OK)
               return Response({"error": "name '{}' is unavailable".format(name)}, status=status.HTTP_400_BAD_REQUEST)
                    

class UserWithProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
     queryset = User.objects.all()
     lookup_field = 'name'
     
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return UserWithProfileDetailSerializer
          elif self.request.method in ('PUT', 'PATCH'):
               return UserWithProfileUpdateSerializer
     
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()
     
     def perform_update(self, serializer):
          return serializer.save()
     
     def update(self, request, *args, **kwargs):
          instance = self.get_object()
          serializer = self.get_serializer(instance, data=request.data, partial=True)
          if serializer.is_valid(raise_exception=True):
               updated_instance = self.perform_update(serializer)
               response_serializer = UserWithProfileDetailSerializer(updated_instance)
               return Response(response_serializer.data, status=status.HTTP_200_OK)
          

class UserWithProfileListAPIView(generics.ListAPIView):
     queryset = User.objects.all()
     serializer_class = UserWithProfileDetailSerializer

class UserDestroyAPIView(generics.DestroyAPIView):
     queryset = User.objects.all()
     serializer_class = UserDetailSerializer
     lookup_field = 'name'
     
     def get_object(self):
          queryset = self.filter_queryset(self.get_queryset())
          pk = self.kwargs.get('pk')

          if pk is not None:
               return get_object_or_404(queryset, pk=pk)
          else:
               return super().get_object()

# apis related to friends
class SendFriendRequestAPIView(APIView):
     def post(self, request):
          data = request.data
          to_user = User.objects.get(name=data['to_user'])
          from_user = User.objects.get(name=data['from_user'])
          
          if to_user != from_user:
               if not FriendRequest.objects.filter(to_user=to_user, from_user=from_user).exists():
                    friend_request = FriendRequest.objects.create(to_user=to_user, from_user=from_user)
                    serializer = FriendRequestDetailSerializer(friend_request)
                    return Response(serializer.data, status=status.HTTP_200_OK)
               return Response({"error": "this friend request is already sent"}, status=status.HTTP_409_CONFLICT)    
          return Response({"error": "sender and receiver is the same"}, status=status.HTTP_400_BAD_REQUEST)
     
class AcceptFriendRequestAPIView(APIView):
     def post(self, request):
          friend_request = FriendRequest.objects.get(pk=request.data['friend_request_id'])
          accepting_user = User.objects.get(name=request.data['user'])
          
          if friend_request.to_user == accepting_user:
               if not friend_request.accepted:
                    friend_request.accepted = True
                    friend_request.save()
                    accepting_user.friends.add(friend_request.from_user)
                    
                    # set last notification as read (just in case)
                    friend_request_notification = Notification.objects.get(related_id=friend_request.pk)
                    if not friend_request_notification.is_read:
                         friend_request_notification.is_read = True
                         friend_request_notification.save()
                    
                    # create notifcation for friend_request_accepted
                    Notification.objects.create(
                         type="friend_request_accepted", 
                         to_user=friend_request.from_user, 
                         related_id= friend_request.pk
                    )
                    
                    serializer = FriendRequestDetailSerializer(friend_request)
                    return Response(serializer.data, status=status.HTTP_200_OK)
               return Response({"error": "this friend request is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "this friend request was not sent to this user"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class UserFriendsListAPIView(generics.ListAPIView):
     serializer_class = UserDetailSerializer
     
     def get_queryset(self):
          user = get_object_or_404(User, name=self.request.data["user"])
          queryset = user.friends.all()
          return queryset
     
     def post(self, request, *args, **kwargs):
          queryset = self.get_queryset()
          serializer = self.serializer_class(queryset, many=True)
          return Response(serializer.data, status=status.HTTP_200_OK)
     
     