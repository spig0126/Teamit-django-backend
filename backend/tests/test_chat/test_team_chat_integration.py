import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from chat.models import TeamChatRoom
from home.asgi import application
from tests.test_team.factories import TeamFactory
from tests.test_user.factories import UserFactory
from tests.test_user.token_test import create_firebase_token

from user.models import User


@pytest.mark.asyncio
@pytest.mark.django_db
class TestTeamChatIntegration():
    async def test_team_all_chatroom_creation(self, mocker):
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay')
        user = await database_sync_to_async(UserFactory.create)()
        team = await database_sync_to_async(TeamFactory.create)(creator=user)
        team_all_chatroom = await database_sync_to_async(TeamChatRoom.objects.get)(team=team, name='전체방')

        # check team_all_chatroom exists
        assert team_all_chatroom
        assert await database_sync_to_async(team_all_chatroom.participants.filter(pk=user.pk).exists)()

        # check enter msg is sent
        mock_fcm.assert_not_called()
        first_msg =  await database_sync_to_async(team_all_chatroom.messages.all().order_by('timestamp').first)()
        # assert

    async def test_websocket_communication(user1_team1, team1, team_all_chatroom, team_communicator):
        user3 = await database_sync_to_async(UserFactory)
        user2 = await database_sync_to_async(User.objects.get)(uid=user3.uid)
        print(user2)
        user = await database_sync_to_async(User.objects.get)(pk=4)
        token = create_firebase_token(user.uid)
        headers = [(b'authorization', f'Bearer {token}'.encode())]
        communicator = WebsocketCommunicator(application, f"/ws/chat-status/", headers)
        connected, subprotocol = await communicator.connect()
        assert connected is True

        await communicator.send_json_to({"type": "change", "chat_type": "private"})
        response = await communicator.receive_json_from()
        assert response['type'] == "private_chatroom_list"
