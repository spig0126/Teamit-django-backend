import pytest
import pytest_asyncio
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from home.asgi import application
from .factories import TeamFactory, TeamMemberFactory
from ..test_chat.factories import InquiryChatRoomFactory
from ..test_user.factories import UserFactory
from ..test_user.token_test import create_firebase_token


@pytest.fixture
def team1(db):
    return TeamFactory()


@pytest.fixture
def team1_member1(db, team1):
    return TeamMemberFactory(team=team1)


@pytest.fixture
def team1_member2(db, team1):
    return TeamMemberFactory(team=team1)


# ---------------------------------------------
@pytest_asyncio.fixture(autouse=True, scope='function')
async def async_inquirer(db):
    inquirer = await sync_to_async(UserFactory.create)()
    yield inquirer
    await sync_to_async(inquirer.delete)()


@pytest_asyncio.fixture(autouse=True, scope='function')
async def async_responder(db):
    responder = await sync_to_async(UserFactory.create)()
    yield responder
    await sync_to_async(responder.delete)()

@pytest_asyncio.fixture(autouse=True, scope='function')
async def async_responder_team(db, async_responder):
    team = await sync_to_async(TeamFactory.create)(creator=async_responder)
    yield team
    await sync_to_async(team.delete)()

@pytest_asyncio.fixture(autouse=True, scope='function')
async def async_inquiry_member(db, async_responder_team):
    member = await sync_to_async(TeamMemberFactory.create)(team=async_responder_team)
    yield member
    await sync_to_async(member.user.delete)()

@pytest_asyncio.fixture(autouse=True, scope='function')
async def async_inquiry_chatroom(db, async_inquirer, async_responder_team):
    chatroom = await sync_to_async(InquiryChatRoomFactory.create)(inquirer=async_inquirer, team=async_responder_team)
    yield chatroom
    await sync_to_async(chatroom.delete)()

@pytest_asyncio.fixture(autouse=True, scope='function')
async def inquirer_inquiry_communicator(db, async_inquirer, async_inquiry_chatroom):
    token = create_firebase_token(async_inquirer.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/inquiry-chat/{async_inquiry_chatroom.pk}/', headers=headers)

