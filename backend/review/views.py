from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.decorators import permission_classes
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from .models import *
from .serializers import *
from .permissions import *

@permission_classes([IsEligibleForReviewer])
class UserReviewListCreateAPIView(generics.ListCreateAPIView):
     def get_serializer_class(self):
          if self.request.method == 'POST':
               return UserReviewCreateUpdateSerializer
          return UserReviewDetailSerializer
     
     def perform_create(self, serializer):
          serializer.save(reviewer=self.request.user)
     
     def get_queryset(self):
          user = self.request.user
          return UserReview.objects.filter(reviewee=user)

@permission_classes([IsReviewer])
class UserReviewRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
     serializer_class = UserReviewCreateUpdateSerializer
     
     def initial(self, request, *args, **kwargs):
          self.review = get_object_or_404(UserReview, pk=self.kwargs.get('pk', None))
          super().initial(request, *args, **kwargs)

     def get_object(self):
          return self.review

     def patch(self, request, *args, **kwargs):
          if self.review.edited:
               return Response({'detail': 'User can edit review only once'}, status=status.HTTP_400_BAD_REQUEST)
          return super().patch(request, *args, **kwargs)
     
@permission_classes([IsReviewee])
class UserReviewCommentCreateAPIView(generics.CreateAPIView):
     serializer_class = UserReviewCommentCreateUpdateSerializer
     queryset = UserReviewComment.objects.all()
     
     def initial(self, request, *args, **kwargs):
          self.review = get_object_or_404(UserReview, pk=request.data.get('review', None))
          super().initial(request, *args, **kwargs)
          
     def create(self, request, *args, **kwargs):
          try:
               return super().create(request, *args, **kwargs)
          except IntegrityError:
               return Response({'detail': 'user can comment only once'}, status=status.HTTP_409_CONFLICT)

@permission_classes([IsReviewee])
class UserReviewCommentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
     serializer_class = UserReviewCommentCreateUpdateSerializer
     queryset = UserReviewComment.objects.all()
     
     def initial(self, request, *args, **kwargs):
          self.comment = get_object_or_404(UserReviewComment, pk=self.kwargs.get('pk', None))
          self.review = self.comment.review
          super().initial(request, *args, **kwargs)
          
     def get_object(self):
          return self.comment

     def patch(self, request, *args, **kwargs):
          if self.comment.edited:
               return Response({'detail': 'User can edit comment only once'}, status=status.HTTP_400_BAD_REQUEST)
          return super().patch(request, *args, **kwargs)