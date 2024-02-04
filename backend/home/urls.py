from django.urls import path, include
from .views import *

urlpatterns = [
    path("api/third-party-login/", ThirdPartyLoginView.as_view()),
    path("api/check-user/", CheckUserWithUID.as_view()),
    path("api/images/", ImageRetrieveAPIView.as_view()),
    path("api/regions/", include("region.urls")),
    path("api/users/", include("user.urls")),
    path("api/positions/", include("position.urls")),
    path("api/interests/", include("interest.urls")),
    path("api/activities/", include("activity.urls")),
    path("api/teams/", include("team.urls")),
    path("api/teams/", include("post.urls")),
    path("api/notifications/", include("notification.urls")),
    path("api/articles/", include("article.urls")),
    path("api/reports/", include("report.urls")),
    path("api/search/", include("search.urls")),
    path("api/devices/", include("fcm_notification.urls")),
    path("api/chat/", include("chat.urls")),

]
