from rest_framework import generics

from .models import *
from .serializers import *
from user.utils import get_user_by_name


class ProfileCardRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = ProfileCardDetailSerializer

    def get_object(self):
        self.user = get_user_by_name(self.kwargs.get('name', ''))
        return self.user.profile_card

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.user
        return context


class ProfileCardRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfileCardUpdateInfoSerializer
        elif self.request.method == 'PATCH':
            return ProfileCardUpdateSerializer

    def get_object(self):
        return self.request.user.profile_card

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['current_profile_card'] = self.get_object()
        return context
