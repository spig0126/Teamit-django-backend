import pytest
from asgiref.sync import sync_to_async

from chat.models import InquiryChatParticipant, InquiryChatRoom, PrivateChatParticipant, PrivateChatRoom
from tests.test_chat.factories import InquiryChatRoomFactory


async def receive_start_msg(communicator):
    is_alone_msg = await communicator.receive_json_from()
    user_roles_msg = await communicator.receive_json_from()
    history_msg = await communicator.receive_json_from()
    return is_alone_msg, user_roles_msg, history_msg


async def send_msg(communicator):
    await communicator.send_json_to({
        "type": "msg",
        "message": {
            "content": "hello"
        }
    })


async def connect_and_receive_start_msg(communicator):
    connected, code = await communicator.connect()
    try:
        assert connected
    except:
        print('Connect error:', code)
        return

    await receive_start_msg(communicator)


@pytest.mark.django_db
def test_create_inquiry_chat_participants_signal(inquiry_chatroom):
    assert inquiry_chatroom.participants.count() == 2
    assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=True).exists()
    assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=False).exists()




@pytest.mark.django_db
class TestInquiryRelatedSignals():
    def test_create_inquiry_chat_participants_signal(self, inquiry_chatroom):
        assert inquiry_chatroom.participants.count() == 2
        assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=True).exists()
        assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=False).exists()

    class TestHandleInquiryChatParticipantDeleteSignal():
        async def exit_announcment_data(self, chatroom, content):
            return {
                "type": "msg",
                "message": {
                    "sender": None,
                    "content": content,
                    "name": "",
                    "avatar": "",
                    "background": "",
                    "unread_cnt": 0,
                    "is_msg": False
                }
            }

        def test_inquiry_chatroom_delete_when_alone_participant_deleted(self, inquiry_chatroom):
            # assume participant is alone
            InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=False).delete()
            assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom).count() == 1

            # check chatroom is deleted when alone participant is deleted
            chatroom_pk = inquiry_chatroom.pk
            InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom).delete()
            assert not InquiryChatRoom.objects.filter(pk=chatroom_pk).exists()
            assert not InquiryChatParticipant.objects.filter(chatroom=chatroom_pk).exists()

        @pytest.mark.asyncio
        async def test_offline_msg_send_when_inquirer_exit(self, async_inquirer, async_inquiry_chatroom,
                                                           responder_inquiry_communicator,
                                                           inquirer_inquiry_communicator):
            await connect_and_receive_start_msg(inquirer_inquiry_communicator)
            await connect_and_receive_start_msg(responder_inquiry_communicator)

            # inquirer exit
            await inquirer_inquiry_communicator.send_json_to({
                "type": "exit"
            })

            # responder receive offine msg
            offline_msg = await responder_inquiry_communicator.receive_json_from()
            assert offline_msg['type'] == 'offline'
            assert offline_msg['message']['user'] == async_inquirer.pk

            # test inquirer participant deleted from db
            assert not await sync_to_async(
                InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=True).exists)()

        @pytest.mark.asyncio
        async def test_offline_msg_send_when_responder_exit(self, async_responder, async_inquiry_chatroom,
                                                           responder_inquiry_communicator,
                                                           inquirer_inquiry_communicator):
            await connect_and_receive_start_msg(inquirer_inquiry_communicator)
            await connect_and_receive_start_msg(responder_inquiry_communicator)
            online_msg = await inquirer_inquiry_communicator.receive_json_from()

            # responder exit
            await responder_inquiry_communicator.send_json_to({
                "type": "exit"
            })

            # inquirer receive offine msg
            offline_msg = await inquirer_inquiry_communicator.receive_json_from()
            assert offline_msg['type'] == 'offline'
            assert offline_msg['message']['user'] == async_responder.pk

            # test responder participant deleted from db
            assert not await sync_to_async(
                InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=False).exists)()

        @pytest.mark.asyncio
        async def test_exit_announcement_msg_send_when_inquirer_exit(self, async_inquiry_chatroom, async_inquirer, inquirer_inquiry_communicator, responder_inquiry_communicator):
            await connect_and_receive_start_msg(inquirer_inquiry_communicator)
            await connect_and_receive_start_msg(responder_inquiry_communicator)

            # inquirer exit
            await inquirer_inquiry_communicator.send_json_to({
                "type": "exit"
            })

            # responder receive offine msg + exit announcement
            offline_msg = await responder_inquiry_communicator.receive_json_from()
            exit_announcement_msg = await responder_inquiry_communicator.receive_json_from()
            assert exit_announcement_msg['type'] == 'msg'

            exit_announcement_msg['message'].pop('timestamp')
            exit_announcement_msg['message'].pop('id')
            assert exit_announcement_msg == await self.exit_announcment_data(async_inquiry_chatroom, f'{async_inquirer.name} 님이 퇴장했습니다')

            # test inquirer participant deleted from db
            assert not await sync_to_async(
                InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=True).exists)()

        @pytest.mark.asyncio
        async def test_exit_announcement_msg_send_when_responder_exit(self, async_inquiry_chatroom, async_inquirer,
                                                                     inquirer_inquiry_communicator,
                                                                     responder_inquiry_communicator):
            await connect_and_receive_start_msg(inquirer_inquiry_communicator)
            await connect_and_receive_start_msg(responder_inquiry_communicator)

            # responder exit
            await responder_inquiry_communicator.send_json_to({
                "type": "exit"
            })

            # inquirer receive online_msg + offine msg + exit announcement
            online_msg = await inquirer_inquiry_communicator.receive_json_from()
            offline_msg = await inquirer_inquiry_communicator.receive_json_from()
            exit_announcement_msg = await inquirer_inquiry_communicator.receive_json_from()
            assert exit_announcement_msg['type'] == 'msg'

            exit_announcement_msg['message'].pop('timestamp')
            exit_announcement_msg['message'].pop('id')
            assert exit_announcement_msg == await self.exit_announcment_data(async_inquiry_chatroom,
                                                                             f'{async_inquiry_chatroom.team_name} 님이 퇴장했습니다')

            # test inquirer participant deleted from db
            assert not await sync_to_async(
                InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=False).exists)()

    class TestDeleteChatParticipantWhenUserDelete():
        def test_participant_instance_deleted_from_db(self, user1):
            InquiryChatRoom.objects.all().delete()
            assert InquiryChatRoom.objects.count() == 0

            inquiry_chatroom1 = InquiryChatRoomFactory(inquirer=user1)
            inquiry_chatroom2 = InquiryChatRoomFactory(inquirer=user1)

            # assume user1 is in two inquiry chatrooms
            assert InquiryChatParticipant.objects.filter(chatroom__inquirer=user1, is_inquirer=True).count() == 2
            assert InquiryChatRoom.objects.filter(inquirer=user1).count() == 2

            user1.delete()

            assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom1).count() == 1
            assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom2).count() == 1
            assert InquiryChatRoom.objects.filter(inquirer=None).count() == 2

        def test_delete_empty_inquiry_chatrooms_when_user_delete(self, user1, team2, inquiry_chatroom):
            assert InquiryChatRoom.objects.filter(pk=inquiry_chatroom.pk).exists()

            user1.delete()
            team2.delete()

            assert not InquiryChatRoom.objects.filter(pk=inquiry_chatroom.pk).exists()

    class TestDeleteChatParticipantWhenTeamDelete():
        def test_participant_instance_deleted_from_db(self, team1):
            InquiryChatRoom.objects.all().delete()
            assert InquiryChatRoom.objects.count() == 0

            inquiry_chatroom1 = InquiryChatRoomFactory(team=team1)
            inquiry_chatroom2 = InquiryChatRoomFactory(team=team1)

            # assume team1 is in two inquiry chatrooms
            assert InquiryChatParticipant.objects.filter(chatroom__team=team1, is_inquirer=False).count() == 2
            assert InquiryChatRoom.objects.filter(team=team1).count() == 2

            team1.delete()

            assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom1).count() == 1
            assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom2).count() == 1
            assert InquiryChatRoom.objects.filter(team=None).count() == 2

@pytest.mark.django_db
class TestPrivateRelatedSignals():
    class TestHandlePrivateChatParticipantDelete():
        def test_private_chatroom_delete_when_alone_participant_deleted(self, private_chatroom, user1, user2):
            # assume participant is alone
            PrivateChatParticipant.objects.filter(chatroom=private_chatroom, user=user2).delete()
            assert PrivateChatParticipant.objects.filter(chatroom=private_chatroom).count() == 1

            # check chatroom is deleted when alone participant is deleted
            chatroom_pk = private_chatroom.pk
            PrivateChatParticipant.objects.filter(chatroom=private_chatroom).delete()
            assert not PrivateChatRoom.objects.filter(pk=chatroom_pk).exists()
            assert not PrivateChatParticipant.objects.filter(chatroom=chatroom_pk).exists()


'''

TEST INQUIRY DELETE
- when participant delete
- when user/team delete

'''
