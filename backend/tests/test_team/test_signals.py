import pytest
from asgiref.sync import sync_to_async

from chat.models import TeamChatRoom
from team.models import Team
from tests.test_team.factories import TeamFactory, TeamMemberFactory
from tests.test_user.factories import UserFactory


@pytest.mark.django_db
class TestHandleTeamCreate():
    def test_team_all_chatroom_is_created(self):
        team = TeamFactory()
        assert TeamChatRoom.objects.get(team=team, name='전체방')


@pytest.mark.django_db
class TestAddNewMemberToAllChatroom():
    def test_new_member_added_to_all_chatroom(self):
        team = TeamFactory()
        user = UserFactory()
        new_member = TeamMemberFactory(team=team, user=user)

        team_all_chatroom = TeamChatRoom.objects.filter(team=team).order_by('created_at').first()
        assert team_all_chatroom.name == '전체방'
        assert user in team.members.all()
        assert user in team_all_chatroom.participants.all()


@pytest.mark.django_db
class TestHandleUserTeamMemberDelete():
    def test_responder_change_when_member_delete(self, team1, team1_member1):
        team1.permission.responder = team1_member1.user
        team1.save()
        assert team1.responder == team1_member1.user

        team1_member1.delete()

        team1.refresh_from_db()
        assert team1.responder == team1.creator

    def test_change_team_creator_when_creator_delete(self, team1, team1_member1, team1_member2):
        team1_pk = team1.pk
        team1.creator.delete()

        team1.refresh_from_db()
        assert team1.creator in team1.members.all()

    def test_team_delete_when_creator_alone(self, team1):
        team1_pk = team1.pk
        team1.creator.delete()

        assert not Team.objects.filter(pk=team1_pk).exists()

    def test_responder_change_when_creator_delete(self, team1, team1_member1):
        assert team1.responder == team1.creator

        team1.creator.delete()

        team1.refresh_from_db()

        assert team1.creator == team1_member1.user
        assert team1.responder == team1.creator

    @pytest.mark.asyncio
    async def test_announcement_msg_sent_when_responder_delete(self, inquirer_inquiry_communicator, async_responder):
        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected

        # receive start msgs
        await inquirer_inquiry_communicator.receive_json_from()
        await inquirer_inquiry_communicator.receive_json_from()
        await inquirer_inquiry_communicator.receive_json_from()

        # delete responder
        await sync_to_async(async_responder.delete)()

        # receive announcement msg that states responder has changed
        announcement_msg = await inquirer_inquiry_communicator.receive_json_from()
        assert announcement_msg['type'] == 'msg'
        assert announcement_msg['message']['is_msg'] is False
        assert announcement_msg['message']['content'] == '문의자가 변경되었습니다'

