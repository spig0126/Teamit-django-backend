import asyncio

import pytest
from channels.db import database_sync_to_async
import pytest_asyncio
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from django.db.models import Q

from chat.models import InquiryChatRoom, PrivateChatParticipant
from chat.status_consumers import ChatStatusConsumer
from home.asgi import application
from team.models import TeamMembers
from tests.test_chat.factories import InquiryChatRoomFactory, PrivateChatRoomFactory, TeamChatRoomFactory
from tests.test_team.factories import TeamFactory, TeamMemberFactory
from tests.test_user.factories import UserFactory
from tests.test_user.token_test import create_firebase_token

from user.models import User
from chat.models import InquiryChatParticipant


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_communication(team1):
    user = await database_sync_to_async(User.objects.get)(pk=4)
    token = create_firebase_token(user3.uid)
    headers = [(b'authorization', f'Bearer {token}'.encode())]
    communicator = WebsocketCommunicator(application, f"/ws/chat-status/", headers)
    connected, subprotocol = await communicator.connect()
    assert connected is True

    await communicator.send_json_to({"type": "change", "chat_type": "private"})
    response = await communicator.receive_json_from()
    assert response['type'] == "private_chatroom_list"


@pytest.mark.asyncio
@pytest.mark.django_db
class TestDBRelatedFunctions():
    class TestFetchPrivateChatrooms():
        async def test_result(self, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "private",
            })

            response = await status_communicator.receive_json_from()

            chatrooms = response['message']
            assert len(chatrooms) == 2
            assert chatrooms[0]['updated_at'] > chatrooms[1]['updated_at']

        async def test_blocked_users_excluded(self, async_user1, async_user2, async_user3, status_communicator):
            await sync_to_async(async_user1.blocked_users.add)(async_user3)
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "private",
            })

            response = await status_communicator.receive_json_from()

            chatrooms = response['message']
            assert len(chatrooms) == 1
            assert chatrooms[0]['name'] == async_user2.name

    class TestFetchInquiryChatrooms():
        @pytest_asyncio.fixture(autouse=True)
        async def team1(self, async_user1):
            team = await sync_to_async(TeamFactory.create)(creator=async_user1)
            yield team
            await sync_to_async(team.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team2(self, async_user2):
            team = await sync_to_async(TeamFactory.create)(creator=async_user2)
            yield team
            await sync_to_async(team.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def inquiry_chatroom1(self, async_user2, team1):
            chatroom = await sync_to_async(InquiryChatRoomFactory.create)(inquirer=async_user2, team=team1)
            yield chatroom
            await sync_to_async(chatroom.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def inquiry_chatroom2(self, async_user1, team2):
            chatroom = await sync_to_async(InquiryChatRoomFactory.create)(inquirer=async_user1, team=team2)
            yield chatroom
            await sync_to_async(chatroom.delete)()

        async def test_result(self, async_user1, async_user2, team1, team2, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "all"
            })

            response = await status_communicator.receive_json_from()

            chatrooms = response['message']
            assert len(chatrooms) == 2
            assert chatrooms[0]['updated_at'] > chatrooms[1]['updated_at']
            for chatroom in chatrooms:
                print(chatroom)

    class TestFetchTeamChatrooms():
        @pytest_asyncio.fixture(autouse=True)
        async def team1_member1(self, async_user1, async_team1):
            member = await sync_to_async(TeamMembers.objects.get)(team=async_team1, user=async_user1)
            yield member
            await sync_to_async(member.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team1_member2(self, async_user2, async_team1):
            member = await sync_to_async(TeamMemberFactory.create)(team=async_team1, user=async_user2)
            yield member
            await sync_to_async(member.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team_chatroom1(self, async_user1, async_user2, async_team1, team1_member1, team1_member2):
            chatroom = await sync_to_async(TeamChatRoomFactory.create)(team=async_team1,
                                                                       add_participants=[[async_user1, team1_member1],
                                                                                         [async_user2, team1_member2]])
            yield chatroom
            await sync_to_async(chatroom.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team_chatroom2(self, async_user2, async_team1, team1_member2):
            chatroom = await sync_to_async(TeamChatRoomFactory.create)(team=async_team1,
                                                                       add_participants=[[async_user2, team1_member2]])
            yield chatroom
            await sync_to_async(chatroom.delete)()

        async def test_result(self, async_team1, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "team",
                "team_id": async_team1.pk
            })

            response = await status_communicator.receive_json_from()

            chatrooms = response['message']
            assert len(chatrooms) == 2
            assert chatrooms[0]['updated_at'] > chatrooms[1]['updated_at']
            for chatroom in chatrooms:
                print(chatroom)


@pytest.mark.asyncio
@pytest.mark.django_db
class TestChangeMsg():
    class TestChangeInquiry():
        @pytest_asyncio.fixture(autouse=True)
        async def team1(self, async_user1):
            team = await sync_to_async(TeamFactory.create)(creator=async_user1)
            yield team
            await sync_to_async(team.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team2(self, async_user2):
            team = await sync_to_async(TeamFactory.create)(creator=async_user2)
            yield team
            await sync_to_async(team.delete)()

        @pytest_asyncio.fixture(autouse=True, scope='function')
        async def inquiry_chatroom1(self, async_user2, team1):
            chatroom = await sync_to_async(InquiryChatRoomFactory.create)(inquirer=async_user2, team=team1)
            yield chatroom
            await sync_to_async(chatroom.delete)()

        @pytest_asyncio.fixture(autouse=True, scope='function')
        async def inquiry_chatroom2(self, async_user1, team2):
            chatroom = await sync_to_async(InquiryChatRoomFactory.create)(inquirer=async_user1, team=team2)
            yield chatroom
            await sync_to_async(chatroom.delete)()

        async def test_change_inquiry_all(self, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "all"
            })

            response = await status_communicator.receive_json_from()

            assert response['type'] == 'inquiry_chatroom_list'
            assert len(response['message']) == 2

            await status_communicator.disconnect()

        async def test_change_inquiry_responder(self, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "responder"
            })

            response = await status_communicator.receive_json_from()

            assert response['type'] == 'inquiry_chatroom_list'
            assert len(response['message']) == 1
            print(response['message'])

            await status_communicator.disconnect()

        async def test_change_inquiry_inquirer(self, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "inquirer"
            })

            response = await status_communicator.receive_json_from()

            assert response['type'] == 'inquiry_chatroom_list'
            assert len(response['message']) == 1
            print(response['message'])

            await status_communicator.disconnect()

    class TestChangePrivate():
        async def test_change_private(self, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "private",
            })

            response = await status_communicator.receive_json_from()

            assert response['type'] == 'private_chatroom_list'
            chatrooms = response['message']
            assert len(chatrooms) == 2

    class TestChangeTeam():
        @pytest_asyncio.fixture(autouse=True)
        async def team1_member1(self, async_user1, async_team1):
            member = await sync_to_async(TeamMembers.objects.get)(team=async_team1, user=async_user1)
            yield member
            await sync_to_async(member.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team1_member2(self, async_user2, async_team1):
            member = await sync_to_async(TeamMemberFactory.create)(team=async_team1, user=async_user2)
            yield member
            await sync_to_async(member.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team_chatroom1(self, async_user1, async_user2, async_team1, team1_member1, team1_member2):
            chatroom = await sync_to_async(TeamChatRoomFactory.create)(team=async_team1,
                                                                       add_participants=[[async_user1, team1_member1],
                                                                                         [async_user2, team1_member2]])
            yield chatroom
            await sync_to_async(chatroom.delete)()

        @pytest_asyncio.fixture(autouse=True)
        async def team_chatroom2(self, async_user2, async_team1, team1_member2):
            chatroom = await sync_to_async(TeamChatRoomFactory.create)(team=async_team1,
                                                                       add_participants=[[async_user2, team1_member2]])
            yield chatroom
            await sync_to_async(chatroom.delete)()

        async def test_result(self, async_team1, status_communicator):
            connected, _ = await status_communicator.connect()
            assert connected

            await status_communicator.send_json_to({
                "type": "change",
                "chat_type": "team",
                "team_id": async_team1.pk
            })

            response = await status_communicator.receive_json_from()

            assert response['type'] == 'team_chatroom_list'
            chatrooms = response['message']
            assert len(chatrooms) == 2


@pytest.mark.asyncio
@pytest.mark.django_db
class TestUpdateAlarmStatusMsg():
    class TestInquiryChatroomAlarmStatusUpdate():
        @pytest_asyncio.fixture(autouse=True)
        async def inquirer_participant(self, async_inquiry_chatroom):
            return await sync_to_async(InquiryChatParticipant.objects.get)(chatroom=async_inquiry_chatroom,
                                                                           is_inquirer=True)

        @pytest_asyncio.fixture(autouse=True)
        async def responder_participant(self, async_inquiry_chatroom):
            return await sync_to_async(InquiryChatParticipant.objects.get)(chatroom=async_inquiry_chatroom,
                                                                           is_inquirer=False)

        async def test_inquirer_chatroom_alarm_on_status_update(self,
                                                                async_inquiry_chatroom,
                                                                inquirer_status_communicator,
                                                                inquirer_participant,
                                                                responder_participant):
            assert inquirer_participant.alarm_on is True
            assert responder_participant.alarm_on is True

            connected, _ = await inquirer_status_communicator.connect()
            assert connected

            await inquirer_status_communicator.send_json_to({
                "type": "update_alarm_status",
                "chat_type": "inquiry",
                "chatroom_id": async_inquiry_chatroom.pk
            })

            assert await inquirer_status_communicator.receive_nothing()

            await sync_to_async(inquirer_participant.refresh_from_db)()
            assert inquirer_participant.alarm_on is False
            assert responder_participant.alarm_on is True

            await inquirer_status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "inquirer"
            })

            response = await inquirer_status_communicator.receive_json_from()
            assert response['message'][0]['alarm_on'] is False

        async def test_responder_chatroom_alarm_on_status_update(self,
                                                                 async_inquiry_chatroom,
                                                                 responder_status_communicator,
                                                                 inquirer_participant,
                                                                 responder_participant):
            assert responder_participant.alarm_on is True
            assert inquirer_participant.alarm_on is True

            connected, _ = await responder_status_communicator.connect()
            assert connected

            await responder_status_communicator.send_json_to({
                "type": "update_alarm_status",
                "chat_type": "inquiry",
                "chatroom_id": async_inquiry_chatroom.pk
            })

            assert await responder_status_communicator.receive_nothing()

            await sync_to_async(responder_participant.refresh_from_db)()
            assert responder_participant.alarm_on is False
            assert inquirer_participant.alarm_on is True

            await responder_status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "responder"
            })

            response = await responder_status_communicator.receive_json_from()
            assert response['message'][0]['alarm_on'] is False


@pytest.mark.asyncio
@pytest.mark.django_db
class TestExitMsg():
    class TestInquiryChatRoomExit():
        async def receive_start_msgs(self, communicator):
            is_alone_msg = await communicator.receive_json_from()
            user_roles = await communicator.receive_json_from()
            history_msg = await communicator.receive_json_from()

        async def test_participant_deletion_and_exit_successful_msg(self, async_inquirer, async_inquiry_chatroom,
                                                   inquirer_status_communicator, responder_inquiry_communicator):
            connected, _ = await inquirer_status_communicator.connect()
            assert connected
            connected, _ = await responder_inquiry_communicator.connect()
            assert connected
            await self.receive_start_msgs(responder_inquiry_communicator)

            await inquirer_status_communicator.send_json_to({
                "type": "exit",
                "chat_type": "inquiry",
                "chatroom_id": async_inquiry_chatroom.pk
            })

            response = await inquirer_status_communicator.receive_json_from()
            assert response['type'] == 'exit_successful'
            assert response['message'] is True

            assert not await sync_to_async(
                InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=True).exists)()
            assert await sync_to_async(
                InquiryChatRoom.objects.filter(pk=async_inquiry_chatroom.pk, inquirer=async_inquirer).exists)()

        async def test_exit_announcement_msg_sent_to_inquiry_chatroom(self, async_inquirer, async_inquiry_chatroom,
                                                         inquirer_status_communicator,
                                                         responder_inquiry_communicator):
            connected, _ = await inquirer_status_communicator.connect()
            assert connected
            connected, _ = await responder_inquiry_communicator.connect()
            assert connected
            await self.receive_start_msgs(responder_inquiry_communicator)

            await inquirer_status_communicator.send_json_to({
                "type": "exit",
                "chat_type": "inquiry",
                "chatroom_id": async_inquiry_chatroom.pk
            })

            offling_msg = await responder_inquiry_communicator.receive_json_from()
            response = await responder_inquiry_communicator.receive_json_from()
            assert response['type'] == 'msg'
            assert response['message']['is_msg'] is False
            assert response['message']['unread_cnt'] is 0
            assert response['message']['content'] == f'{async_inquirer.name} 님이 퇴장했습니다'

            assert await sync_to_async(InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom).count)() == 1

    class TestPrivateChatRoomExit():
        async def receive_start_msgs(self, communicator):
            is_alone_msg = await communicator.receive_json_from()
            history_msg = await communicator.receive_json_from()

        async def test_participant_deleted_from_db(self, async_user1, async_user2, async_private_chatroom_12,
                                                   status_communicator, private_communicator):
            connected, _ = await status_communicator.connect()
            assert connected
            connected, _ = await private_communicator.connect()
            assert connected
            await self.receive_start_msgs(private_communicator)

            await status_communicator.send_json_to({
                "type": "exit",
                "chat_type": "private",
                "chatroom_id": async_private_chatroom_12.pk
            })

            response = await status_communicator.receive_json_from()
            assert response['type'] == 'exit_successful'
            assert response['message'] is True

            assert not await sync_to_async(
                PrivateChatParticipant.objects.filter(chatroom=async_private_chatroom_12, user=async_user1).exists)()
            assert await sync_to_async(
                PrivateChatParticipant.objects.filter(chatroom=async_private_chatroom_12, user=async_user2).exists)()

        async def test_exit_msg_sent_to_private_chatroom(self, async_private_chatroom_12, status_communicator,
                                                         private_communicator):
            connected, _ = await status_communicator.connect()
            assert connected
            connected, _ = await private_communicator.connect()
            assert connected
            await self.receive_start_msgs(private_communicator)

            await status_communicator.send_json_to({
                "type": "exit",
                "chat_type": "private",
                "chatroom_id": async_private_chatroom_12.pk
            })

            response = await private_communicator.receive_json_from()
            assert response['type'] == 'msg'
            assert response['message']['is_msg'] is False
            assert response['message']['unread_cnt'] is 0
