import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from chat.models import TeamChatParticipant, TeamChatRoom
from home.asgi import application
from team.models import TeamMembers
from tests.test_user.factories import UserFactory
from tests.test_user.token_test import create_firebase_token

from user.models import User



@pytest.mark.asyncio
@pytest.mark.django_db
class TestTeamConsumers():
    async def test_websocket_communication(self, async_user1_communicator):
        connected, subprotocol = await async_user1_communicator.connect()
        try:
            assert connected is True
        except Exception as e:
            print(f"exception: {e}")
            print(f"connected: {connected}, subprotocol: {subprotocol}")


@pytest.mark.asyncio
@pytest.mark.django_db
class TestMsg():
    msg = {
        "type": "msg",
        "message": {
            "content": "hello everyone"
        }
    }

    async def refresh(self, instance):
        await sync_to_async(instance.refresh_from_db)()

    async def receive_start_msgs(self, communicator):
        is_alone_msg = await communicator.receive_json_from()
        history_msg = await communicator.receive_json_from()

    async def conne    msg = {
        "type": "msg",
        "message": {
            "content": "hello everyone"
        }
    }

    async def refresh(self, instance):
        await sync_to_async(instance.refresh_from_db)()

    async def receive_start_msgs(self, communicator):
        is_alone_msg = await communicator.receive_json_from()
        history_msg = await communicator.receive_json_from()

    async def connect_to(self, communicator):
        connected, _ = await communicator.connect()
        assert connected is True

    async def user_send_message_to(self, communicator):
        await self.connect_to(communicator)
        await communicator.send_json_to(self.msg)
        await self.receive_start_msgs(communicator)

    async def test_msg_creation(self, async_user1, async_team1, user1_team_communicator):
        await self.user_send_message_to(user1_team_communicator)

        member = await sync_to_async(TeamMembers.objects.get)(team=async_team1, user=async_user1)
        response = await user1_team_communicator.receive_json_from()
        msg = response['message']
        assert response['type'] == 'msg'
        assert msg['content'] == 'hello everyone'
        assert msg['name'] == await sync_to_async(lambda: member.name)()
        assert msg['unread_cnt'] == 2

    async def test_chatroom_last_msg_update(self, async_team_all_chatroom, user1_team_communicator):
        await self.user_send_message_to(user1_team_communicator)
        response = await user1_team_communicator.receive_json_from()

        await self.refresh(async_team_all_chatroom)
        assert async_team_all_chatroom.last_msg == self.msg['message']['content']

    async def test_offline_participant_unread_cnt_update(self, async_user2, async_user3, async_team_all_chatroom, user1_team_communicator, user2_team_communicator):
        await self.user_send_message_to(user1_team_communicator)
        await user1_team_communicator.receive_json_from()

        p2 = await sync_to_async(TeamChatParticipant.objects.get)(chatroom=async_team_all_chatroom, user=async_user2)
        p3 = await sync_to_async(TeamChatParticipant.objects.get)(chatroom=async_team_all_chatroom, user=async_user3)

        assert p2.unread_cnt == 1
        assert p3.unread_cnt == 1

        await self.user_send_message_to(user2_team_communicator)
        await user2_team_communicator.receive_json_from()

        await self.refresh(p2)
        await self.refresh(p3)

        assert p2.unread_cnt == 0
        assert p3.unread_cnt == 2


    async def user_send_message_to(self, communicator):
        await communicator.send_json_to(self.msg)
        await self.connect_and_send_test_message(communicator)
        await self.receive_start_msgs(communicator)

    async def test_msg_creation(self, async_user1, async_team1, user1_team_communicator):
        await self.user_send_message_to(user1_team_communicator)

        member = await sync_to_async(TeamMembers.objects.get)(team=async_team1, user=async_user1)
        response = await user1_team_communicator.receive_json_from()
        msg = response['message']
        assert response['type'] == 'msg'
        assert msg['content'] == 'hello everyone'
        assert msg['name'] == await sync_to_async(lambda: member.name)()
        assert msg['unread_cnt'] == 2

    async def test_chatroom_last_msg_update(self, async_team_all_chatroom, user1_team_communicator):
        await self.user_send_message_to(user1_team_communicator)
        response = await user1_team_communicator.receive_json_from()

        await self.refresh(async_team_all_chatroom)
        assert async_team_all_chatroom.last_msg == self.msg['message']['content']

    async def test_offline_participant_unread_cnt_update(self, async_user2, async_user3, async_team_all_chatroom, user1_team_communicator, user2_team_communicator):
        await self.user_send_message_to(user1_team_communicator)
        await user1_team_communicator.receive_json_from()

        p2 = await sync_to_async(TeamChatParticipant.objects.get)(chatroom=async_team_all_chatroom, user=async_user2)
        p3 = await sync_to_async(TeamChatParticipant.objects.get)(chatroom=async_team_all_chatroom, user=async_user3)

        assert p2.unread_cnt == 1
        assert p3.unread_cnt == 1

        await self.user_send_message_to(user2_team_communicator)
        await user2_team_communicator.receive_json_from()

        await self.refresh(p2)
        await self.refresh(p3)

        assert p2.unread_cnt == 0
        assert p3.unread_cnt == 2

    async def test_group_message_sent(self, async_p1, user1_team_communicator, user2_team_communicator):
        # p2 connect
        await self.connect_to(user2_team_communicator)
        await self.receive_start_msgs(user2_team_communicator)

        # p1 connect and send msg
        await self.user_send_message_to(user1_team_communicator)

        response =  await user2_team_communicator.receive_json_from()
        msg = response['message']

        assert response['type'] == 'msg'
        assert msg['content'] == 'hello everyone'
        assert msg['name'] == await sync_to_async(lambda: async_p1.member.name)()
        assert msg['unread_cnt'] == 2
