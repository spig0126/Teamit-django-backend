import pytest

from chat.models import InquiryChatParticipant
from chat.serializers import InquiryChatRoomDetailSerializer
from tests.test_chat.factories import InquiryChatRoomFactory


@pytest.mark.django_db
class TestInquiryChatSerializers():
    class TestInquiryChatRoomDetailSerializer():
        def test_inquirer_chatroom(self, user1, inquiry_chatroom):
            participant = InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=True)
            serializer = InquiryChatRoomDetailSerializer(participant)

            expected_data = {
                'id': inquiry_chatroom.id,
                'name': inquiry_chatroom.inquirer_chatroom_name,
                'avatar': inquiry_chatroom.inquirer_avatar,
                'background': inquiry_chatroom.inquirer_background,
                'last_msg': inquiry_chatroom.last_msg,
                'unread_cnt': 0,
                'updated_at': inquiry_chatroom.updated_at,
                'alarm_on': participant.alarm_on
            }
            assert serializer.data == expected_data

        def test_team_chatroom(self, team2, inquiry_chatroom):
            participant = InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=False)
            serializer = InquiryChatRoomDetailSerializer(participant)

            expected_data = {
                'id': inquiry_chatroom.id,
                'name': inquiry_chatroom.team_chatroom_name,
                'avatar': inquiry_chatroom.team_image,
                'background': inquiry_chatroom.team_background,
                'last_msg': inquiry_chatroom.last_msg,
                'unread_cnt': 0,
                'updated_at': inquiry_chatroom.updated_at,
                'alarm_on': participant.alarm_on
            }
            assert serializer.data == expected_data
