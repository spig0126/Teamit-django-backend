from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from django.utils import timezone

from .models import *
from .serializers import *
from team.models import TeamMembers
from team.permissions import IsTeamMemberPermission
from team.utils import get_team_by_pk


@permission_classes([IsTeamMemberPermission])
class TeamNotificationListAPIView(generics.ListAPIView):
    serializer_class = TeamNotificationListSerializer

    def initial(self, request, *args, **kwargs):
        self.team = get_team_by_pk(self.kwargs.get('team_pk'))
        super().initial(request, *args, **kwargs)

    def get_queryset(self):
        member = TeamMembers.objects.get(team=self.team, user=self.request.user)

        # update member's team notification reading status
        member.noti_unread_cnt = 0
        member.save()

        is_creator = self.request.user == self.team.creator

        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        team_notifications = TeamNotification.objects.filter(to_team=self.team)
        team_notifications.filter(created_at__lt=cutoff_date).delete()
        return {'is_creator': is_creator, 'team_notifications': team_notifications}

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationDetailSerializer

    def get_queryset(self):
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        notificiations = Notification.objects.filter(to_user=self.request.user)
        notificiations.filter(created_at__lt=cutoff_date).delete()
        notificiations.update(is_read=True)
        return notificiations


class UnreadNotificationsStatusAPIView(APIView):
    def get(self, request):
        if request.user.notifications.filter(is_read=False).exists():
            return Response({"unread": True}, status=status.HTTP_200_OK)
        return Response({"unread": False}, status=status.HTTP_200_OK)
