from rest_framework import viewsets

from .models import *
from .serializers import *

# class UserViewSet(viewsets.ModelViewSet):
#      queryset = User.objects.all()
#      serializer_class = UserSerializer

#      def create(self, request, *args, **kwargs):
#           data = request.data
#           print(kwargs)
#           # position_names = data.pop('position_names')
#           # interest_names = data.pop('interest_names')
#           # user = User.objects.create(**data)
#           # positions = []
#           # interests = []
#           # for position_name in position_names:
#           #      positions.append(Position.objects.get(name=position_name))
#           # for interest_name in interest_names:
#           #      interests.append(Interest.objects.get(name=interest_name))
#           # # user.
          
#           # Continue with the default create functionality if validation passes
#           return super().create(request, *args, **kwargs)
     
'''
GET /api/mymodels/ - List all instances of MyModel
POST /api/mymodels/ - Create a new instance of MyModel
GET /api/mymodels/{pk}/ - Retrieve a specific instance of MyModel by primary key (pk)
PUT /api/mymodels/{pk}/ - Update a specific instance of MyModel by primary key (pk)
PATCH /api/mymodels/{pk}/ - Partially update a specific instance of MyModel by primary key (pk)
DELETE /api/mymodels/{pk}/ - Delete a specific instance of MyModel by primary key (pk)
'''