from django.urls import path

from .views import *

urlpatterns = [
     path("info/", UserReviewOptionsDetailAPIView.as_view()), 
     path("", UserReviewCreateAPIView.as_view(), name='create user review'), 
     path("<str:name>/", UserReviewListAPIView.as_view(), name='create, list user review'), 
     path("<int:pk>/", UserReviewRetrieveUpdateDestroyAPIView.as_view(), name='update, destroy user review'), 
     path("comments/", UserReviewCommentCreateAPIView.as_view(), name='create, list user review'), 
     path("comments/<int:pk>/", UserReviewCommentRetrieveUpdateDestroyAPIView.as_view(), name='update, destroy user review comment'), 
]