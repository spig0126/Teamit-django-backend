import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from chat.private_consumers import PrivateChatConsumer
from home.asgi import application
from tests.test_chat.factories import PrivateChatRoomFactory
from tests.test_user.factories import UserFactory
from tests.test_user.token_test import create_firebase_token
from asgiref.sync import sync_to_async

from user.models import User


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_communication(user13_headers):
    communicator = WebsocketCommunicator(application, f"/ws/chat-status/", user13_headers)
    connected, subprotocol = await communicator.connect()
    assert connected is True

    await communicator.send_json_to({"type": "change", "chat_type": "private"})
    response = await communicator.receive_json_from()
    assert response['type'] == "private_chatroom_list"
