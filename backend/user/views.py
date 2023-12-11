from django.shortcuts import get_object_or_404
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count

from .models import *
from .serializers import *
from activity.models import Activity
from region.models import Province, City
from notification.models import Notification

class UserWithProfileDetailAPIView(generics.GenericAPIView):
     queryset = UserProfile.objects.all()
     serializer_class = UserProfileCreateSerializer

     def get_serializer_class(self):
          if self.request.method == 'GET':
               return MyProfileDetailSerializer
          else:
               return UserProfileCreateSerializer
     
     def post(self, request, *args, **kwargs):    # create user
          serializer = self.get_serializer(data=request.data)
          if serializer.is_valid(raise_exception=True):
               serializer.save()
               return Response({"message": "User & UserProfile succesfully created"}, status=status.HTTP_200_OK)
     
     def get(self, request, *args, **kwargs):     # get my profile
          user_pk = int(self.request.headers.get('UserID'))
          user = get_object_or_404(User, pk=user_pk)
          serializer = self.get_serializer(user)
          return Response(serializer.data, status=status.HTTP_200_OK)
          
     
class UserWithProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
     queryset = User.objects.all()
     
     def get_serializer_class(self):
          if self.request.method == 'GET':
               return UserWithProfileDetailSerializer
          elif self.request.method in ('PUT', 'PATCH'):
               return UserWithProfileUpdateSerializer
     
     def perform_update(self, serializer):
          return serializer.save()
     
     def update(self, request, *args, **kwargs):  # update my profile
          user_pk = int(request.headers.get('UserID'))
          if user_pk != self.kwargs.get('pk'):
               raise PermissionDenied("user not allowed to update this profile")
          else:
               instance = self.get_object()
               serializer = self.get_serializer(instance, data=request.data, partial=True)
               if serializer.is_valid(raise_exception=True):
                    updated_instance = self.perform_update(serializer)
                    print(updated_instance)
                    response_serializer = MyProfileDetailSerializer(updated_instance)
                    return Response(response_serializer.data, status=status.HTTP_200_OK)
          
class UserDetailAPIView(RetrieveModelMixin, DestroyModelMixin, generics.GenericAPIView):
     queryset = User.objects.all()
     serializer_class = UserDetailSerializer
     
     def get(self, request, *args, **kwargs):
          return self.retrieve(request, *args, **kwargs)
     
     def delete(self,request, *args, **kwargs):
          user_pk = int(request.headers.get('UserID'))
          print(type(user_pk), type(kwargs.get('pk')))
          if user_pk != kwargs.get('pk'):
               raise PermissionDenied("user is not allowed to delete this user")
          return self.destroy(request, *args, **kwargs)

class RecommendedUserListAPIView(generics.ListAPIView):
     serializer_class = RecommendedUserDetailSerializer
     
     def get_queryset(self):
          return User.objects.annotate(like_cnt=Count('liked_by')).order_by('-like_cnt')

class CheckUserNameAvailability(APIView):
     def get(self, request):
          name = request.GET.get('name')
          
          try:
               user = User.objects.get(name=name)
               return Response({"error": "name '{}' is unavailable".format(name)}, status=status.HTTP_400_BAD_REQUEST)
          except:
               return Response({"message": "name '{}' is available".format(name)}, status=status.HTTP_200_OK)
                    
class UserWithProfileListAPIView(generics.ListAPIView):
     queryset = User.objects.all()
     serializer_class = UserWithProfileDetailSerializer

# apis related to friends
class SendFriendRequestAPIView(APIView):
     def post(self, request):
          data = request.data
          to_user = User.objects.get(name=data['to_user'])
          from_user = User.objects.get(name=data['from_user'])
          
          if to_user != from_user: 
               if to_user not in from_user.friends.all():   # if not friend
                    if not FriendRequest.objects.filter(to_user=to_user, from_user=from_user).exists():  # if not sent
                         friend_request = FriendRequest.objects.create(to_user=to_user, from_user=from_user)   # Notification 자동적으로 생성됨
                         serializer = FriendRequestDetailSerializer(friend_request)
                         return Response(serializer.data, status=status.HTTP_200_OK)
                    return Response({"error": "this friend request is already sent"}, status=status.HTTP_208_ALREADY_REPORTED)    
               return Response({"error": "they are already friends"}, status=status.HTTP_409_CONFLICT)    
          return Response({"error": "sender and receiver is the same"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class UnsendFriendRequestAPIView(APIView):
     def post(self, request):
          data = request.data
          to_user = User.objects.get(name=data['to_user'])
          from_user = User.objects.get(name=data['from_user'])
          
          friend_request = get_object_or_404(FriendRequest, to_user=to_user, from_user=from_user, accepted=False)
          notification = get_object_or_404(Notification, related_id=friend_request.pk, type='friend_request')

          friend_request.delete()
          notification.delete()
          return Response({"message": "friend request successfuly unsent"}, status=status.HTTP_200_OK)

class AcceptFriendRequestAPIView(APIView):
     def post(self, request):
          friend_request = get_object_or_404(FriendRequest, pk=request.data['friend_request_id'])
          accepting_user = get_object_or_404(User, name=request.data['user'])
          
          if friend_request.to_user == accepting_user:
               if not friend_request.accepted:
                    try:
                         friend_request.accepted = True
                         
                         # set notification type to "friend_request_accept"
                         friend_request_notification = Notification.objects.get(type="friend_request",related_id=friend_request.pk)
                         friend_request_notification.type = "friend_request_accept"
                         if not friend_request_notification.is_read: # set last notification as read (just in case)
                              friend_request_notification.is_read = True
                         
                         # create notifcation for friend_request_accepted
                         Notification.objects.create(
                              type="friend_request_accepted", 
                              to_user=friend_request.from_user, 
                              related_id= friend_request.pk
                         )
                         
                         serializer = FriendRequestDetailSerializer(friend_request)
                    except:
                         return Response({"error": "unexpected error"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                         friend_request.save()
                         accepting_user.friends.add(friend_request.from_user)
                         friend_request_notification.save()
                         return Response(serializer.data, status=status.HTTP_200_OK)
               return Response({"error": "this friend request is already accepted"}, status=status.HTTP_409_CONFLICT)
          return Response({"error": "this friend request was not sent to this user"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class UnfriendUserAPIView(APIView):
     def post(self, request, *args, **kwargs):
          userA = get_object_or_404(User, name=request.data['userA'])
          userB = get_object_or_404(User, name=request.data['userB'])
          
          try:
               friend_request = FriendRequest.objects.get(to_user=userA, from_user=userB)
          except:
               friend_request = FriendRequest.objects.get(to_user=userB, from_user=userA)
               
          Notification.objects.filter(related_id=friend_request.pk, type__startswith='f').delete()
          friend_request.delete()
          userA.friends.remove(userB)
          userB.friends.remove(userA)
          
          return Response({"message": "unfriend request successful"}, status=status.HTTP_204_NO_CONTENT)

class DeclineFriendRequestAPIView(APIView):
     def post(self, request):
          friend_request_id = request.data['friend_request_id']
          friend_request = get_object_or_404(FriendRequest, pk=friend_request_id)
          accepting_user = get_object_or_404(User, name=request.data['user'])
          if friend_request.to_user == accepting_user:
               Notification.objects.get(type="friend_request", related_id=friend_request_id).delete()
               FriendRequest.objects.get(pk=friend_request_id).delete()
               return Response({"message": "friend request successfully declined"}, status=status.HTTP_200_OK)
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
     
# likes related apis
class UserLikesListAPIView(APIView):
     def get(self, request):
          user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          user_likes = [obj.to_user for obj in UserLikes.objects.filter(from_user=user)]
          serializer = UserLikesListSerializer(user_likes)
          return Response(serializer.data, status=status.HTTP_200_OK)

class LikeUnlikeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          from_user = get_object_or_404(User, pk=self.request.headers.get('UserID'))
          to_user = get_object_or_404(User, pk=self.kwargs.get('pk'))
          try:
               user_like = UserLikes.objects.get(from_user=from_user, to_user=to_user)
               user_like.delete()
               return Response({"message": "user unliked"}, status=status.HTTP_204_NO_CONTENT)
          except:
               UserLikes.objects.create(from_user=from_user, to_user=to_user)
               return Response({"message": "user liked"}, status=status.HTTP_201_CREATED) 