from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from rest_framework.mixins import RetrieveModelMixin
from django.db import connections
from django.db import transaction

from .models import *
from .serializers import *
from .exceptions import *
from .permissions import *
# from .index import UserIndex
from . import client
from .utils import *
from activity.models import Activity
from region.models import Province, City
from notification.models import Notification
from fcm_notification.utils import send_fcm_to_user

class UserWithProfileDetailAPIView(RetrieveModelMixin, generics.GenericAPIView):
     queryset = UserProfile.objects.all()

     def initial(self, request, *args, **kwargs):
          if self.request.method == 'POST':
               request.skip_authentication = True
          super().initial(request, *args, **kwargs)
          
     def get_serializer_class(self):
          if self.request.method == 'GET':
               simple = self.request.query_params.get('simple', None) == 'true'
               return UserSimpleDetailSerializer if simple else MyProfileDetailSerializer
          return UserProfileCreateSerializer
     
     def post(self, request, *args, **kwargs):    # create user
          serializer = self.get_serializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          serializer.save()
          return Response({"message": "User & UserProfile succesfully created"}, status=status.HTTP_200_OK)
     
     def get_object(self):
          return self.request.user
     
     def get(self, request, *args, **kwargs):
          return self.retrieve(request, *args, **kwargs)
     
@permission_classes([CanEditUser])
class UserWithProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
     lookup_field = 'name'
     
     def get_object(self):
          name = self.kwargs.get(self.lookup_field)
          try:
               obj = User.objects.select_related('profile').get(name=name)
               return obj
          except User.DoesNotExist:
               raise UserNotFoundWithName()

     def get_serializer_context(self):
          context = super().get_serializer_context()
          if self.request.method == 'GET':
               context['viewer_user'] = self.request.user
          return context
     
     def get_serializer_class(self):
          if self.request.method == 'PATCH':
               return UserWithProfileUpdateSerializer
          if self.request.method == 'GET':
               if self.request.user.name == self.kwargs.get('name'):
                    return MyProfileDetailSerializer
               return UserWithProfileDetailSerializer
          
class UpdatePageInfoRetrieveAPIView(APIView):
     def get(self, request, *args, **kwargs):
          data = {
               'regions': ProvinceWithCitiesSerializer(Province.objects.all(), many=True).data,
               'positions': Position.objects.all().values_list('name', flat=True),
               'activities': Activity.objects.all().values_list("name", flat=True),
               'interests': Interest.objects.all().values_list("name", flat=True),
               'tools': Tool.objects.all().values_list('name', flat=True),
          }
          return Response(data, status=status.HTTP_200_OK)
     
@permission_classes([CanEditUser])
class UserDetailAPIView(generics.DestroyAPIView):
     queryset = User.objects.all()
     serializer_class = UserDetailSerializer
     lookup_field = 'name'
          
     def get_object(self):
          name = self.kwargs.get(self.lookup_field)
          return get_object_or_404(User, name=name)


class RecommendedUserListAPIView(generics.ListAPIView):
     serializer_class = RecommendedUserDetailSerializer
     def get_serializer_context(self):
          context = super().get_serializer_context()
          if self.request.method == 'GET':
               context['viewer_user'] = self.request.user
          return context

     def get_queryset(self):
          user = self.request.user
          filters = []
          for attribute in ['interest', 'position', 'activity', 'city']:
               values = getattr(user, f'{attribute}_names')
               filters.extend([f'{attribute}_names:"{value}"' for value in values])

          results = client.perform_filtered_search(' OR '.join(filters))

          searched_pks = {int(result['objectID']) for result in results}
          blocked_user_pks = set(self.request.user.blocked_users.all().values_list('pk', flat=True))
          recommended_pks = searched_pks - blocked_user_pks - {user.pk}
          
          if len(recommended_pks) < 50:
               exclude_pks = recommended_pks.union(blocked_user_pks).union({user.pk})
               random_user_pks = User.objects.exclude(pk__in=exclude_pks).values_list('pk', flat=True)[:50 - len(recommended_pks)]
               recommended_pks.union(random_user_pks)
               
          return User.objects.filter(pk__in=recommended_pks).order_by('?')[:50]

class CheckUserNameAvailability(APIView):
     def initial(self, request, *args, **kwargs):
          request.skip_authentication = True
          super().initial(request, *args, **kwargs)

     def get(self, request):
          name = request.GET.get('name')
          
          try:
               user = User.objects.get(name=name)
               return Response({"error": "name '{}' is unavailable".format(name)}, status=status.HTTP_400_BAD_REQUEST)
          except:
               return Response({"message": "name '{}' is available".format(name)}, status=status.HTTP_200_OK)
                    
class UserWithProfileListAPIView(generics.ListAPIView):
     serializer_class = UserWithProfileDetailSerializer
     
     def get_serializer_context(self):
          context = super().get_serializer_context()
          if self.request.method == 'GET':
               context['viewer_user'] = self.request.user
          return context
     
     def get_queryset(self):
          users = User.objects.all().exclude(pk=self.request.user.pk)
          return users
          
class UserImageUpdateAPIView(generics.UpdateAPIView):
     queryset = User.objects.all()
     serializer_class = UserImageUpdateSerializer
     
     def get_object(self):
          return self.request.user


# apis related to friends
class SendFriendRequestAPIView(APIView):
     @transaction.atomic
     def post(self, request, name):
          to_user = get_user_by_name(name)
          from_user = request.user
          
          if to_user != from_user: 
               if to_user not in from_user.friends.all():   # if not friend
                    if not FriendRequest.objects.filter(to_user=to_user, from_user=from_user).exists():  # if not sent
                         if not FriendRequest.objects.filter(to_user=from_user, from_user=to_user).exists():  # if not recieved friend request from the other user
                              friend_request = FriendRequest.objects.create(to_user=to_user, from_user=from_user)   # Notification 자동적으로 생성됨
                              serializer = FriendRequestDetailSerializer(friend_request)
                              return Response(serializer.data, status=status.HTTP_200_OK)
                         return Response({"detail": "there is a friend request sent from the other user"}, status=status.HTTP_403_FORBIDDEN) 
                    return Response({"detail": "this friend request is already sent"}, status=status.HTTP_208_ALREADY_REPORTED)    
               return Response({"detail": "they are already friends"}, status=status.HTTP_409_CONFLICT)    
          return Response({"detail": "sender and receiver is the same"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

class UnsendFriendRequestAPIView(APIView):
     @transaction.atomic
     def post(self, request, name):
          to_user = get_user_by_name(name)
          from_user = request.user
          friend_request = get_friend_request(from_user, to_user, False)
          notification = get_object_or_404(Notification, related_id=friend_request.pk, type='friend_request')

          friend_request.delete()
          notification.delete()
          return Response({"message": "friend request successfuly unsent"}, status=status.HTTP_200_OK)

class AcceptFriendRequestAPIView(APIView):
     @transaction.atomic
     def post(self, request, name):
          from_user = get_user_by_name(name)
          to_user = request.user
          friend_request = get_friend_request(from_user, to_user, False)
          
          if not friend_request.accepted:
               try:
                    friend_request.accepted = True
                    
                    # set notification type to "friend_request_accept"
                    friend_request_notification = Notification.objects.get(type="friend_request",related_id=friend_request.pk)
                    friend_request_notification.type = "friend_request_accept"

                         
                    serializer = FriendRequestDetailSerializer(friend_request)
               except Exception as e:
                    return Response({"error": f'unexpected error - {e}'}, status=status.HTTP_400_BAD_REQUEST)
               else:
                    friend_request.save()
                    to_user.friends.add(from_user)
                    friend_request_notification.save()
                    
                    # if user is not blocked
                    if to_user not in from_user.blocked_users.all(): 
                         # create notifcation for friend_request_accepted
                         Notification.objects.create(
                              type="friend_request_accepted", 
                              to_user=friend_request.from_user, 
                              related_id= friend_request.pk
                         )
                         
                         # send fcm notification to user
                         title = '친구 요청 수락'
                         body = f'{to_user.name} 님이 친구 요청을 수락하였습니다.\n친구 공개 정보를 확인해보세요.'
                         data = {
                              "page": "user_notification"
                         }
                         send_fcm_to_user(from_user, title, body, data)
                    
                    return Response(serializer.data, status=status.HTTP_200_OK)
          return Response({"error": "this friend request is already accepted"}, status=status.HTTP_409_CONFLICT)

class UnfriendUserAPIView(APIView):
     @transaction.atomic
     def post(self, request, name):
          userA = request.user
          userB = get_user_by_name(name)
          
          friend_request = None
          if FriendRequest.objects.filter(to_user=userA, from_user=userB).exists():
               friend_request = FriendRequest.objects.get(to_user=userA, from_user=userB)
          else:
               try:
                    friend_request = FriendRequest.objects.get(to_user=userB, from_user=userA)
               except FriendRequest.DoesNotExist():
                    raise FriendRequestNotFound()

          Notification.objects.filter(related_id=friend_request.pk, type__startswith='f').delete()
          friend_request.delete()
          userA.friends.remove(userB)
          userB.friends.remove(userA)
          
          return Response({"message": "unfriend request successful"}, status=status.HTTP_204_NO_CONTENT)

class DeclineFriendRequestAPIView(APIView):
     @transaction.atomic
     def post(self, request, name):
          from_user = get_user_by_name(name)
          to_user = request.user
          friend_request = get_friend_request(from_user, to_user, False)
          notification = get_object_or_404(Notification, related_id=friend_request.pk, type='friend_request')
          
          notification.delete()
          friend_request.delete()
          
          return Response({"message": "friend request successfully declined"}, status=status.HTTP_200_OK)


class UserFriendsListAPIView(generics.ListAPIView):
     serializer_class = UserDetailSerializer
     
     def get_queryset(self):
          return self.request.user.friends.all()
     
# likes related apis
class UserLikesListAPIView(APIView):
     def get(self, request):
          user_likes = [obj.to_user for obj in UserLikes.objects.filter(from_user=request.user)]
          
          context = {'viewer_user': request.user}
          serializer = UserLikesListSerializer(user_likes, context=context)
          return Response(serializer.data, status=status.HTTP_200_OK)

class LikeUnlikeAPIView(APIView):
     def put(self, request, *args, **kwargs):
          from_user = request.user
          to_user = get_object_or_404(User, name=kwargs.get('name'))
          try:
               user_like = UserLikes.objects.get(from_user=from_user, to_user=to_user)
               user_like.delete()
               return Response({"message": "user unliked"}, status=status.HTTP_204_NO_CONTENT)
          except:
               UserLikes.objects.create(from_user=from_user, to_user=to_user)
               return Response({"message": "user liked"}, status=status.HTTP_201_CREATED) 
          
# block user related apis
class BlockUnblockUserAPIView(APIView):
     def put(self, request, *args, **kwargs):
          from_user = request.user
          to_user = get_object_or_404(User, name=kwargs.get('name', None))
          
          if to_user == from_user:
               return Response({"detail": "cannot block oneslef"}, status=status.HTTP_409_CONFLICT)
          if to_user in from_user.blocked_users.all():
               from_user.blocked_users.remove(to_user)
               return Response({"message": "user unblocked"}, status=status.HTTP_204_NO_CONTENT)
          else:
               from_user.blocked_users.add(to_user)
               return Response({"message": "user blocked"}, status=status.HTTP_201_CREATED) 

class BlockedUserListAPIView(generics.ListAPIView):
     serializer_class = UserDetailSerializer
     
     def get_queryset(self):
          return self.request.user.blocked_users.all()
     
# search api
class UserSearchAPIView(generics.ListAPIView):
     serializer_class = UserDetailSerializer

     def get_queryset(self):
          # Retrieve the search query from the request
          query = self.request.query_params.get('q', '')
          blocked_user_pks = set(self.request.user.blocked_users.all().values_list('pk', flat=True))
          
          if query:
               results = client.perform_search(query)
               pks = {int(result['objectID']) for result in results}
               
               # exclude blocked users
               pks -=  blocked_user_pks
               
               users =  User.objects.filter(pk__in=pks)
          else:
               # exclude blocked users
               users = User.objects.exclude(pk__in=blocked_user_pks)
          return users

class FriendSearchAPIView(generics.ListAPIView):
     serializer_class = UserDetailSerializer

     def get_queryset(self):
          # Retrieve the search query from the request
          query = self.request.query_params.get('q', '')
          
          user = self.request.user
          friends = user.friends.all()
          blocked_user_pks = set(user.blocked_users.all().values_list('pk', flat=True))
     
          if query:
               results = client.perform_search(query)
               pks = set([int(result['objectID']) for result in results['hits']])
               
               # filter friends
               friend_pks = set(friends.values_list('pk', flat=True))
               filtered_friend_pks = friend_pks & pks
               
               # exclude blocked users
               filtered_friend_pks -= blocked_user_pks
               
               friends = friends.filter(pk__in=filtered_friend_pks)
          else:
               friends = friends.exclude(pk__in=blocked_user_pks)
          return friends
