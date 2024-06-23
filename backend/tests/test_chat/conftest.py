import pytest
from channels.testing import WebsocketCommunicator
import pytest_asyncio
from asgiref.sync import sync_to_async

from chat.models import TeamChatRoom, TeamChatParticipant, InquiryChatParticipant
from home.asgi import application
from tests.test_chat.factories import PrivateChatRoomFactory, TeamChatRoomFactory, InquiryChatRoomFactory
from tests.test_team.factories import TeamFactory, TeamMemberFactory
from tests.test_user.factories import UserFactory
from tests.test_user.token_test import create_firebase_token
from user.models import User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def user1(db):
    return UserFactory()


@pytest.fixture
def user2(db):
    return UserFactory()


@pytest.fixture
def user13(db):
    return User.objects.get(pk=13)


@pytest.fixture
def team1(db):
    return TeamFactory()


@pytest.fixture
def team2(db):
    return TeamFactory()


@pytest.fixture
def member1(db, team1, user1):
    return TeamMemberFactory(team=team1, user=user1)


@pytest.fixture
def member2(db, team1, user2):
    return TeamMemberFactory(team=team1, user=user2)


@pytest.fixture
def team_chatroom(db, user1, user2, member1, member2):
    return TeamChatRoomFactory(add_participants=[[user1, member1], [user2, member2]])


@pytest.fixture
def private_chatroom(db):
    return PrivateChatRoomFactory(add_participants=[user1, user2])


@pytest.fixture
def inquiry_chatroom(db, user1, team2):
    return InquiryChatRoomFactory(inquirer=user1, team=team2)


@pytest.fixture
def private_communicator(db):
    user = User.objects.get(pk=4)
    other_user = UserFactory()
    private_chatroom = PrivateChatRoomFactory(add_participants=[user, other_user])
    token = create_firebase_token(user.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/private-chat/{private_chatroom.pk}/', headers=headers)


@pytest.fixture
def user13_headers(db, user13):
    token = create_firebase_token(user13.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return headers


# -----------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def async_user1(db):
    user = await sync_to_async(UserFactory.create)()
    yield user
    await sync_to_async(user.delete)()


@pytest_asyncio.fixture(autouse=True)
async def async_user2(db):
    user = await sync_to_async(UserFactory.create)()
    yield user
    await sync_to_async(user.delete)()


@pytest_asyncio.fixture(autouse=True)
async def async_user3(db):
    user = await sync_to_async(UserFactory.create)()
    yield user
    await sync_to_async(user.delete)()


@pytest_asyncio.fixture(autouse=True)
async def async_team1(db, async_user1):
    team = await sync_to_async(TeamFactory.create)(creator=async_user1)
    yield team
    await sync_to_async(team.delete)()


@pytest_asyncio.fixture(autouse=True)
async def async_team2(db, async_user2):
    team = await sync_to_async(TeamFactory.create)(creator=async_user2)
    yield team
    await sync_to_async(team.delete)()


@pytest_asyncio.fixture(autouse=True)
async def async_team1_all_chatroom(db, async_team1):
    team_all_chatroom = await sync_to_async(TeamChatRoom.objects.get)(team=async_team1, name='전체방')
    yield team_all_chatroom
    await sync_to_async(team_all_chatroom.delete)()


'''
PRIVATE CHATROOM RELATED
'''

@pytest_asyncio.fixture(autouse=True)
async def async_private_chatroom_12(db, async_user1, async_user2):
    chatroom = await sync_to_async(PrivateChatRoomFactory.create)(add_participants=[async_user1, async_user2])
    yield chatroom
    await sync_to_async(chatroom.delete)()

@pytest_asyncio.fixture(autouse=True)
async def async_private_chatroom_13(db, async_user1, async_user3):
    chatroom = await sync_to_async(PrivateChatRoomFactory.create)(add_participants=[async_user1, async_user3])
    yield chatroom
    await sync_to_async(chatroom.delete)()


@pytest_asyncio.fixture(autouse=True)
async def private_communicator(db, async_user1, async_private_chatroom_12):
    token = create_firebase_token(async_user1.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/private-chat/{async_private_chatroom_12.pk}/', headers=headers)




'''
INQUIRY CHATROOM RELATED
'''

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
async def inquirer_status_communicator(db, async_inquirer):
    token = create_firebase_token(async_inquirer.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/chat-status/', headers=headers)


@pytest_asyncio.fixture(autouse=True, scope='function')
async def responder_status_communicator(db, async_responder):
    token = create_firebase_token(async_responder.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/chat-status/', headers=headers)


@pytest_asyncio.fixture(autouse=True, scope='function')
async def responder_team_inquiry_status_communicator(db, async_responder, async_responder_team):
    token = create_firebase_token(async_responder.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/team-inquiry-status/{async_responder_team.pk}/', headers=headers)


@pytest_asyncio.fixture(autouse=True, scope='function')
async def member_inquiry_communicator(db, async_inquiry_member, async_inquiry_chatroom):
    token = create_firebase_token(async_inquiry_member.user.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/inquiry-chat/{async_inquiry_chatroom.pk}/', headers=headers)


@pytest_asyncio.fixture(autouse=True, scope='function')
async def inquirer_inquiry_communicator(db, async_inquirer, async_inquiry_chatroom):
    token = create_firebase_token(async_inquirer.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/inquiry-chat/{async_inquiry_chatroom.pk}/', headers=headers)


@pytest_asyncio.fixture(autouse=True, scope='function')
async def responder_inquiry_communicator(db, async_responder, async_inquiry_chatroom):
    token = create_firebase_token(async_responder.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/inquiry-chat/{async_inquiry_chatroom.pk}/', headers=headers)

'''
COMMUNICATOR RELATED
'''
@pytest_asyncio.fixture(autouse=True)
async def team_communicator(db, async_user1, async_team1_all_chatroom):
    token = create_firebase_token(async_user1.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/team-chat/{async_team1_all_chatroom.pk}/', headers=headers)


@pytest_asyncio.fixture(autouse=True)
async def status_communicator(db, async_user1):
    token = create_firebase_token(async_user1.uid)
    headers = [
        (b'authorization', f'Bearer {token}'.encode())
    ]
    return WebsocketCommunicator(application, f'/ws/chat-status/', headers=headers)
