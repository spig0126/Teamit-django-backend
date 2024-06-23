from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import TeamPermission, TeamMembers, Team
from chat.models import TeamChatRoom, TeamChatParticipant, InquiryChatRoom
from user.models import User
from chat.serializers import InquiryMessageCreateSerializer, InquiryMessageSerializer


@receiver(pre_delete, sender=User)
@receiver(pre_delete, sender=TeamMembers)
def handle_user_team_member_delete(sender, instance, **kwargs):
    if isinstance(instance, User):
        change_team_creator_when_creator_delete(instance)
        Team.objects.filter(creator=instance).delete()
    elif isinstance(instance, TeamMembers):
        if instance.user == instance.team.creator:
            update_team_responder_to_creator(instance.team)


@receiver(post_save, sender=Team)
def handle_team_create(sender, instance, created, **kwargs):
    if created:
        create_team_permission(instance)
        create_team_all_chatroom(instance)


@receiver(post_save, sender=TeamPermission)
def alert_responder_change(sender, instance, created, **kwargs):
    if not created:
        with transaction.atomic():
            send_inquiry_chatrooms_announcement(instance.team)


@receiver(post_save, sender=TeamMembers)
def add_new_member_to_all_chatroom(sender, instance, created, **kwargs):
    if created:
        with transaction.atomic():
            add_member_to_all_chatroom(instance)


################## team permissions related #################################
def change_team_creator_when_creator_delete(user):
    '''
     탈퇴한 사용자가 팀장일 경우 -> 한 멤버 무작위로 찾아 팀장으로 설정. 다른 멤버 없음 팀 삭제
     '''
    with transaction.atomic():
        teams = Team.objects.filter(creator=user)
        for team in teams:
            if team.members.all().count() == 1:
                continue
            other_member = TeamMembers.objects.filter(team=team).exclude(user=user).first()
            team.creator = other_member.user
            team.save()
            update_team_responder_to_creator(team)


def update_team_responder_to_creator(team):
    '''
     탈퇴한 멤버가 responder일 경우 -> responder를 팀장으로 바꾸기
     '''
    TeamPermission.objects.filter(team=team).update(responder=team.creator)


def create_team_permission(team):
    TeamPermission.objects.create(team=team, responder=team.creator)


############### default team chatroom related ########################
def create_team_all_chatroom(team):
    with transaction.atomic():
        TeamChatRoom.objects.create(
            team=team,
            name='전체방',
            background='0xff00FFD1'
        )


def add_member_to_all_chatroom(member):
    chatroom = TeamChatRoom.objects.filter(team=member.team).order_by('created_at').first()
    if chatroom and not chatroom.participants.filter(pk=member.user.pk).exists():
        TeamChatParticipant.objects.create(
            chatroom=chatroom,
            user=member.user,
            member=member
        )


################ utilities ############################
def send_inquiry_chatrooms_announcement(team):
    for chatroom in InquiryChatRoom.objects.filter(team=team):
        send_inquiry_chatroom_announcement(chatroom, '문의자가 변경되었습니다')


def send_inquiry_chatroom_announcement(chatroom, content):
    announcement = {
        'chatroom': chatroom.id,
        'content': content,
        'is_msg': False
    }
    serializer = InquiryMessageCreateSerializer(data=announcement)
    if serializer.is_valid(raise_exception=True):
        message_instance = serializer.save()
        message = InquiryMessageSerializer(message_instance).data
        channel_layer = get_channel_layer()
        chatroom_name = f'inquiry_chat_{chatroom.id}'
        async_to_sync(channel_layer.group_send)(
            chatroom_name,
            {
                'type': 'msg',
                'message': message
            }
        )
