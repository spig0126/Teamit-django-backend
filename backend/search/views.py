# from rest_framework import generics

# from .index import UserIndex
# from . import client
# from user.models import User
# from user.serializers import UserDetailSerializer

# class UserSearchAPIView(generics.ListAPIView):
#     serializer_class = UserDetailSerializer

#     def get_queryset(self):
#           # Retrieve the search query from the request
#           query = self.request.query_params.get('q')

#           if query:
#                results = client.perform_search(query)
#                pks = set([result['objectID'] for result in results['hits']])
#                user = self.request.user
               
#                # exclude user itself and blocked users
#                pks.discard(user.uid)
#                pks.discard(user.blocked_users.all().values_list('uid', flat=True))
               
#                return User.objects.filter(uid__in=pks)
#           else:
#                return User.objects.all()
     