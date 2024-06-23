import asyncio

import pytest
from asgiref.sync import sync_to_async
from unittest.mock import AsyncMock
import pytest_asyncio

from chat.models import InquiryChatParticipant, InquiryMessage, InquiryRoleType, InquiryChatRoom
from tests.test_chat.factories import InquiryMessageFactory
from tests.test_team.factories import TeamMemberFactory


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


async def connect_and_send_message_to(communicator):
    connected, code = await communicator.connect()
    try:
        assert connected
    except:
        print('Connect error:', code)
        return

    await receive_start_msg(communicator)

    await send_msg(communicator)


@pytest.mark.django_db
@pytest.mark.asyncio
class TestConnectAndStartMsgs():
    """
    testing functions:
    - get_chatroom_and_participants_info()
    - participant_was_offline()
    - update_participant_online()
    - update_online_participants()
    - join_chatroom()
    - online()
    """

    async def cnt_online_participants(self, chatroom):
        return await sync_to_async(
            InquiryChatParticipant.objects.filter(chatroom=chatroom, is_online=True).count)()

    async def is_unread_cnt_0(self, chatroom, is_inquirer):
        return not any(await sync_to_async(
            lambda: list(
                InquiryChatParticipant.objects.filter(chatroom=chatroom, is_inquirer=is_inquirer).values_list(
                    'unread_cnt', flat=True)))())

    async def test_participant_connect(self, async_responder, async_inquiry_chatroom, inquirer_inquiry_communicator,
                                       responder_inquiry_communicator):
        await sync_to_async(InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom).update)(
            is_online=False,
            unread_cnt=0)
        assert await self.cnt_online_participants(async_inquiry_chatroom) == 0
        assert await self.is_unread_cnt_0(async_inquiry_chatroom, True)

        # inquirer connect
        connected, _ = await inquirer_inquiry_communicator.connect()

        assert connected

        # inquirer: recieve start msgs(is_alone, user_roles, last_30_messages)
        is_alone_msg, user_roles_msg, history_msg = await receive_start_msg(inquirer_inquiry_communicator)
        assert is_alone_msg['type'] == 'is_alone'
        assert is_alone_msg['message'] is True
        assert user_roles_msg['type'] == 'user_roles'
        assert user_roles_msg['message'] == {'is_inquirer': True, 'is_responder': False, 'is_member': False}
        assert history_msg['type'] == 'history'

        assert await self.cnt_online_participants(async_inquiry_chatroom) == 1
        assert await self.is_unread_cnt_0(async_inquiry_chatroom, True)

        # responder connect
        connected, _ = await responder_inquiry_communicator.connect()
        assert connected

        # responder: recieve start msgs(is_alone, user_roles, last_30_messages)
        is_alone_msg, user_roles_msg, history_msg = await receive_start_msg(responder_inquiry_communicator)
        assert is_alone_msg['type'] == 'is_alone'
        assert is_alone_msg['message'] is False
        assert user_roles_msg['type'] == 'user_roles'
        assert user_roles_msg['message'] == {'is_inquirer': False, 'is_responder': True, 'is_member': True}
        assert history_msg['type'] == 'history'

        assert await self.cnt_online_participants(async_inquiry_chatroom) == 2
        assert await self.is_unread_cnt_0(async_inquiry_chatroom, False)

        # inquirer receive online msg
        online_msg = await inquirer_inquiry_communicator.receive_json_from()
        assert online_msg['type'] == 'online'
        assert online_msg['message']['user'] == async_responder.pk

    async def test_member_connect(self, async_inquiry_chatroom, member_inquiry_communicator,
                                  inquirer_inquiry_communicator):
        connected, _ = await member_inquiry_communicator.connect()
        assert connected
        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected

        is_alone_msg, user_roles_msg, history_msg = await receive_start_msg(member_inquiry_communicator)
        assert is_alone_msg['type'] == 'is_alone'
        assert is_alone_msg['message'] is True
        assert user_roles_msg['type'] == 'user_roles'
        assert user_roles_msg['message'] == {'is_inquirer': False, 'is_responder': False, 'is_member': True}
        assert history_msg['type'] == 'history'

        # inquirer don't receive 'online' msg
        await receive_start_msg(inquirer_inquiry_communicator)
        assert await inquirer_inquiry_communicator.receive_nothing()

        # check no participants are marked as online
        assert await self.cnt_online_participants(async_inquiry_chatroom) == 1


@pytest.mark.django_db
@pytest.mark.asyncio
class TestDisconnect():
    async def test_mark_as_offline_when_participant_disconnect(self, async_inquirer, async_inquiry_chatroom,
                                                               inquirer_inquiry_communicator,
                                                               responder_inquiry_communicator):
        assert await sync_to_async(
            InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_online=True).count)() == 0

        # inquirer and responder connect
        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected
        connected, _ = await responder_inquiry_communicator.connect()
        assert connected

        await receive_start_msg(inquirer_inquiry_communicator)
        await receive_start_msg(responder_inquiry_communicator)

        assert await sync_to_async(
            InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_online=True).count)() == 2

        # inquirer disconnect
        await inquirer_inquiry_communicator.disconnect()

        # check participant successfully offline
        offline_msg = await responder_inquiry_communicator.receive_json_from()
        assert offline_msg['type'] == 'offline'
        assert offline_msg['message']['user'] == async_inquirer.pk
        await sync_to_async(
            InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_online=True).count)() == 1

    async def test_mark_as_offline_when_member_disconnect(self, inquirer_inquiry_communicator,
                                                          member_inquiry_communicator):
        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected
        connected, _ = await member_inquiry_communicator.connect()
        assert connected

        await receive_start_msg(inquirer_inquiry_communicator)
        await receive_start_msg(member_inquiry_communicator)

        await member_inquiry_communicator.disconnect()

        assert await inquirer_inquiry_communicator.receive_nothing()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestHandleMessage():
    class TestInquirer():
        async def test_create_message(self, async_inquiry_chatroom, inquirer_inquiry_communicator):
            await connect_and_send_message_to(inquirer_inquiry_communicator)

            await inquirer_inquiry_communicator.receive_json_from()

            assert await sync_to_async(InquiryMessage.objects.filter(chatroom=async_inquiry_chatroom,
                                                                     sender=InquiryRoleType.INQUIRER).exists)()
            msg_instance = await sync_to_async(InquiryMessage.objects.get)(chatroom=async_inquiry_chatroom,
                                                                           sender=InquiryRoleType.INQUIRER)
            assert msg_instance.is_msg
            assert msg_instance.content == 'hello'

        async def test_update_chatroom_last_msg_and_unread_cnt(self, async_inquiry_chatroom,
                                                               inquirer_inquiry_communicator):
            await connect_and_send_message_to(inquirer_inquiry_communicator)

            await inquirer_inquiry_communicator.receive_json_from()

            await sync_to_async(async_inquiry_chatroom.refresh_from_db)()
            assert async_inquiry_chatroom.last_msg == 'hello'

            responder_participant = await sync_to_async(InquiryChatParticipant.objects.get)(
                chatroom=async_inquiry_chatroom, is_inquirer=False)
            assert responder_participant.unread_cnt == 1

        async def test_send_status_message(self, inquirer_inquiry_communicator, responder_status_communicator,
                                           responder_team_inquiry_status_communicator, async_inquiry_chatroom):
            # connect to status communicators and receive start messages
            connected, _ = await responder_team_inquiry_status_communicator.connect()
            assert connected
            inquiry_chatroom_list_msg = await responder_team_inquiry_status_communicator.receive_json_from()

            connected, _ = await responder_status_communicator.connect()
            assert connected
            await responder_status_communicator.send_json_to({
                "type": "change",
                "chat_type": "inquiry",
                "filter": "all"
            })
            inquiry_chatroom_list_msg = await responder_status_communicator.receive_json_from()

            await connect_and_send_message_to(inquirer_inquiry_communicator)

            # test status_msgs were successfully sent
            user_status_msg_data = {
                'type': 'update_chatroom',
                'chat_type': 'inquiry',
                'message': {
                    'id': async_inquiry_chatroom.pk,
                    'name': '',
                    'avatar': '',
                    'background': '',
                    'last_msg': 'hello',
                    'update_unread_cnt': True,
                    # updated_at
                }
            }
            team_status_msg_data = {
                'type': 'update_chatroom',
                'message': {
                    'id': async_inquiry_chatroom.pk,
                    'name': '',
                    'last_msg': 'hello',
                }
            }

            status_msg = await responder_status_communicator.receive_json_from()
            status_msg['message'].pop('updated_at')
            assert status_msg == user_status_msg_data

            status_msg = await responder_team_inquiry_status_communicator.receive_json_from()
            status_msg['message'].pop('updated_at')
            assert status_msg == team_status_msg_data

        async def test_send_offline_participants_fcm(self, mocker, async_responder, async_inquiry_chatroom,
                                                     inquirer_inquiry_communicator):
            mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay', new_callable=AsyncMock)

            await connect_and_send_message_to(inquirer_inquiry_communicator)
            await asyncio.sleep(10)
            expected_title = async_inquiry_chatroom.team_chatroom_name
            expected_body = 'hello'
            expected_data = {
                'page': 'chat',
                'chatroom_name': expected_title,
                'chatroom_id': str(async_inquiry_chatroom.pk),
                'chat_type': 'inquiry'
            }
            mock_fcm.assert_called_once_with(async_responder.pk, expected_title, expected_body, expected_data)

        async def test_not_send_offline_participants_fcm_when_alarm_off(self, mocker, async_inquiry_chatroom,
                                                                        inquirer_inquiry_communicator):
            mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay', new_callable=AsyncMock)

            # set responder's alarm off
            await sync_to_async(
                InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=False).update)(
                alarm_on=False)

            # send msg to responder
            await connect_and_send_message_to(inquirer_inquiry_communicator)
            await asyncio.sleep(10)

            mock_fcm.assert_not_called()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestSendLast30Messages():
    async def create_messages(self, chatroom):
        messages = []
        for i in range(63):
            sender = 'T' if i % 2 == 0 else 'I'
            msg = await sync_to_async(InquiryMessageFactory.create)(chatroom=chatroom, sender=sender,
                                                                    content=i)
            messages.append(msg)
        return messages

    async def delete_messages(self, messages):
        for m in messages:
            await sync_to_async(m.delete)()

    async def test_receive_30_messages_when_connect(self, async_inquiry_chatroom, inquirer_inquiry_communicator):
        messages = await self.create_messages(async_inquiry_chatroom)

        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected

        await inquirer_inquiry_communicator.receive_json_from()
        await inquirer_inquiry_communicator.receive_json_from()
        history_msg = await inquirer_inquiry_communicator.receive_json_from()

        assert history_msg['type'] == 'history'
        received_msgs = history_msg['message']

        for i, msg in zip(range(62, 32, -1), received_msgs):
            is_team = i % 2 == 0
            assert msg['content'] == str(i)
            assert msg['sender'] == 'T' if is_team else 'I'
            assert msg['name'] == (
                async_inquiry_chatroom.team_name if is_team else async_inquiry_chatroom.inquirer_name)
            assert msg['avatar'] == (
                async_inquiry_chatroom.team_image if is_team else async_inquiry_chatroom.inquirer_avatar)
            assert msg['background'] == (
                async_inquiry_chatroom.team_background if is_team else async_inquiry_chatroom.inquirer_background)
            assert msg['is_msg']

        await self.delete_messages(messages)

    async def test_history_msg(self, async_inquiry_chatroom, inquirer_inquiry_communicator):
        messages = await self.create_messages(async_inquiry_chatroom)

        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected
        await receive_start_msg(inquirer_inquiry_communicator)

        await inquirer_inquiry_communicator.send_json_to({
            'type': 'history'
        })

        history_msg = await inquirer_inquiry_communicator.receive_json_from()
        received_msgs = history_msg['message']

        assert history_msg['type'] == 'history'
        for i, msg in zip(range(32, 2, -1), received_msgs):
            is_team = i % 2 == 0
            assert msg['content'] == str(i)
            assert msg['sender'] == 'T' if is_team else 'I'
            assert msg['name'] == (
                async_inquiry_chatroom.team_name if is_team else async_inquiry_chatroom.inquirer_name)
            assert msg['avatar'] == (
                async_inquiry_chatroom.team_image if is_team else async_inquiry_chatroom.inquirer_avatar)
            assert msg['background'] == (
                async_inquiry_chatroom.team_background if is_team else async_inquiry_chatroom.inquirer_background)
            assert msg['is_msg']

        await inquirer_inquiry_communicator.send_json_to({
            'type': 'history'
        })
        history_msg = await inquirer_inquiry_communicator.receive_json_from()
        received_msgs = history_msg['message']

        assert history_msg['type'] == 'history'
        for i, msg in zip(range(2, -1, -1), received_msgs):
            is_team = i % 2 == 0
            assert msg['content'] == str(i)
            assert msg['sender'] == 'T' if is_team else 'I'
            assert msg['name'] == (
                async_inquiry_chatroom.team_name if is_team else async_inquiry_chatroom.inquirer_name)
            assert msg['avatar'] == (
                async_inquiry_chatroom.team_image if is_team else async_inquiry_chatroom.inquirer_avatar)
            assert msg['background'] == (
                async_inquiry_chatroom.team_background if is_team else async_inquiry_chatroom.inquirer_background)
            assert msg['is_msg']

        await inquirer_inquiry_communicator.send_json_to({
            'type': 'history'
        })
        history_msg = await inquirer_inquiry_communicator.receive_json_from()
        received_msgs = history_msg['message']
        assert not received_msgs

        await self.delete_messages(messages)

    async def test_unread_cnt(self, async_inquiry_chatroom, inquirer_inquiry_communicator,
                              responder_inquiry_communicator):
        # only inquirer entered
        connected, _ = await inquirer_inquiry_communicator.connect()
        assert connected
        await receive_start_msg(inquirer_inquiry_communicator)

        messages = await self.create_messages(async_inquiry_chatroom)
        await inquirer_inquiry_communicator.send_json_to({
            'type': 'history'
        })
        history_msg = await inquirer_inquiry_communicator.receive_json_from()
        received_msgs = history_msg['message']

        for i, msg in zip(range(32, 2, -1), received_msgs):
            is_team = i % 2 == 0
            assert msg['content'] == str(i)
            assert msg['unread_cnt'] == 1

        # now both inquirer and responder entered
        connected, _ = await responder_inquiry_communicator.connect()
        assert connected
        online_msg = await inquirer_inquiry_communicator.receive_json_from()
        await responder_inquiry_communicator.receive_json_from()
        await responder_inquiry_communicator.receive_json_from()
        history_msg = await responder_inquiry_communicator.receive_json_from()
        received_msgs = history_msg['message']

        for i, msg in zip(range(62, 32, -1), received_msgs):
            is_team = i % 2 == 0
            assert msg['content'] == str(i)
            assert msg['unread_cnt'] == 0

        await inquirer_inquiry_communicator.send_json_to({
            'type': 'history'
        })
        history_msg = await inquirer_inquiry_communicator.receive_json_from()
        received_msgs = history_msg['message']

        for i, msg in zip(range(2, -1, -1), received_msgs):
            is_team = i % 2 == 0
            assert msg['content'] == str(i)
            assert msg['unread_cnt'] == 0


@pytest.mark.django_db
@pytest.mark.asyncio
class TestHandleUpdateAlarmStatus():
    async def test_alarm_change_event(self, async_inquirer, inquirer_inquiry_communicator,
                                      responder_inquiry_communicator, mocker):
        await connect_and_receive_start_msg(inquirer_inquiry_communicator)
        await connect_and_receive_start_msg(responder_inquiry_communicator)
        online_msg = await inquirer_inquiry_communicator.receive_json_from()

        # assume self.alarm_on_participants have both participants
        # test if alarm_on_participants are changed
        await inquirer_inquiry_communicator.send_json_to({
            "type": "update_alarm_status"
        })
        alarm_change_msg = await responder_inquiry_communicator.receive_json_from()
        assert alarm_change_msg['type'] == 'alarm_change'
        assert alarm_change_msg['message']['user'] == async_inquirer.pk
        assert alarm_change_msg['message']['alarm_on'] is False

        # inquirer offline
        await inquirer_inquiry_communicator.disconnect()

        # test inquirer's alarm status by responder sending message and fcm not sent
        mock_fcm = mocker.patch('fcm_notification.tasks.send_fcm_to_user_task.delay', new_callable=AsyncMock)

        await send_msg(responder_inquiry_communicator)
        await asyncio.sleep(10)

        mock_fcm.assert_not_called()

    async def test_participant_alarm_on_change_in_db(self, async_inquiry_chatroom,
                                                     inquirer_inquiry_communicator):
        await connect_and_receive_start_msg(inquirer_inquiry_communicator)
        await inquirer_inquiry_communicator.send_json_to({
            "type": "update_alarm_status"
        })
        alarm_change_msg = await inquirer_inquiry_communicator.receive_json_from()

        assert sync_to_async(InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=True,
                                                                   alarm_on=False).exists)()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestHandleSettings():
    async def test_settings_data(self, async_inquiry_chatroom, inquirer_inquiry_communicator,
                                     responder_inquiry_communicator):
        expected_data = {
            "type": "settings",
            "message": {
                "participant_list": [
                    {
                        "id": async_inquiry_chatroom.inquirer.pk,
                        "name": async_inquiry_chatroom.inquirer_name,
                        "avatar": async_inquiry_chatroom.inquirer_avatar,
                        "background": async_inquiry_chatroom.inquirer_background,
                    },
                    {
                        "id": async_inquiry_chatroom.team.pk,
                        "name": async_inquiry_chatroom.team_name,
                        "avatar": async_inquiry_chatroom.team_image,
                        "background": ""
                    }
                ],
                "alarm_on": True
            }
        }

        # test inquirer settings
        await connect_and_receive_start_msg(inquirer_inquiry_communicator)

        await inquirer_inquiry_communicator.send_json_to({
            "type": "settings"
        })

        settings_msg = await inquirer_inquiry_communicator.receive_json_from()
        assert settings_msg == expected_data

        # test responder settings
        await connect_and_receive_start_msg(responder_inquiry_communicator)

        await responder_inquiry_communicator.send_json_to({
            "type": "settings"
        })

        settings_msg = await responder_inquiry_communicator.receive_json_from()
        settings_msg['message']['participant_list'].reverse()
        assert settings_msg == expected_data

    async def test_settings_alarm_on_after_update_alarm_status(self, async_inquiry_chatroom, inquirer_inquiry_communicator):
        await connect_and_receive_start_msg(inquirer_inquiry_communicator)

        await inquirer_inquiry_communicator.send_json_to({
            "type": "update_alarm_status"
        })

        alarm_change_msg = await inquirer_inquiry_communicator.receive_json_from()

        await inquirer_inquiry_communicator.send_json_to({
            "type": "settings"
        })

        settings_msg = await inquirer_inquiry_communicator.receive_json_from()
        assert settings_msg['message']['alarm_on'] is False



@pytest.mark.django_db
@pytest.mark.asyncio
class TestHandleExit():
    async def test_participant_deletion_and_exit_successful_msg(self, async_inquiry_chatroom, inquirer_inquiry_communicator):
        await connect_and_receive_start_msg(inquirer_inquiry_communicator)

        await inquirer_inquiry_communicator.send_json_to({
            "type": "exit"
        })

        exit_succesfful_msg = await inquirer_inquiry_communicator.receive_json_from()
        assert exit_succesfful_msg['type'] == 'exit_successful'

        assert not await sync_to_async(
            InquiryChatParticipant.objects.filter(chatroom=async_inquiry_chatroom, is_inquirer=True).exists)()


    async def test_exit_announcement_msg(self, inquirer_inquiry_communicator, responder_inquiry_communicator):
        await connect_and_receive_start_msg(inquirer_inquiry_communicator)
        await connect_and_receive_start_msg(responder_inquiry_communicator)

        await inquirer_inquiry_communicator.send_json_to({
            "type": "exit"
        })

        offline_msg = await responder_inquiry_communicator.receive_json_from()
        assert offline_msg['type'] == 'offline'
        exit_announcement_msg = await responder_inquiry_communicator.receive_json_from()
        assert exit_announcement_msg['type'] == 'msg'
        assert exit_announcement_msg['message']['is_msg'] is False

