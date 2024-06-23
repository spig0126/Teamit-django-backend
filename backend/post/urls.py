from django.urls import path

from .views import *

urlpatterns = [
    # team posts
    path("<int:team_pk>/posts/", TeamPostListCreateAPIView.as_view()),  # create, list
    path("<int:team_pk>/posts/<int:post_pk>/", TeamPostDetailAPIView.as_view()),  # update, delete, get
    path("<int:team_pk>/posts/<int:post_pk>/viewed/", ToggleViewedStatus.as_view()),
    path("<int:team_pk>/posts/<int:post_pk>/viewers/", TeamPostViewerListAPIView.as_view()),

    # team post comments
    path("<int:team_pk>/posts/<int:post_pk>/comments/", TeamPostCommenCreateAPIView.as_view()),  # create
    path("<int:team_pk>/posts/<int:post_pk>/comments/<int:comment_pk>/", TeamPostCommenDestroyAPIView.as_view()),
]
