import pytest
from django.utils import timezone
from django.core.files.storage import default_storage

from chat.models import InquiryChatParticipant, InquiryRoleType, InquiryChatRoom
from tests.test_chat.factories import TeamMessageFactory, InquiryMessageFactory


@pytest.mark.django_db
class TestPrivateChatModels():
    def test_private_chat_room_creation(self, private_chatroom):
        assert private_chatroom.id is not None
        assert not private_chatroom.last_msg
        assert private_chatroom.created_at <= timezone.now()
        assert private_chatroom.updated_at <= timezone.now()

        private_chatroom.save()
        assert private_chatroom.created_at <= private_chatroom.updated_at

    def test_private_chat_room_participant_names(self, user1, user2, private_chatroom):
        assert private_chatroom.participant_names == f'{user1.name}, {user2.name}'

    def test_private_chat_participant_creation(self, user1, user2, private_chatroom):
        assert user1 in private_chatroom.participants.all()
        assert user2 in private_chatroom.participants.all()
        assert private_chatroom in user1.private_chat_rooms.all()
        assert private_chatroom in user2.private_chat_rooms.all()

    def test_private_chat_participant_properties(self, user1, user2, private_chatroom):
        pass


@pytest.mark.django_db
class TestTeamChatModels():
    class TestProperties():
        def test_name_property(self, user1, member1, team_chatroom):
            tm = TeamMessageFactory(chatroom=team_chatroom, user=user1, member=member1)
            member1.custom_name = 'custom name'
            member1.save()

            assert tm.name == 'custom name'
            assert tm.name == member1.name

            member1.delete()
            tm.refresh_from_db()

            assert tm.member is None
            assert tm.name == user1.name

            user1.delete()
            tm.refresh_from_db()

            assert tm.user is None
            assert tm.name == '(알 수 없음)'

            tm_not_msg = TeamMessageFactory(is_msg=False)

            assert tm_not_msg.name == ''

        def test_avatar_property(self, user1, member1, team_chatroom):
            tm = TeamMessageFactory(chatroom=team_chatroom, user=user1, member=member1)

            assert tm.avatar == user1.avatar.url

            user1.delete()
            tm.refresh_from_db()

            assert tm.user is None
            assert tm.avatar == default_storage.url('avatars/default.png')

            tm_not_msg = TeamMessageFactory(is_msg=False)

            assert tm_not_msg.avatar == ''

        def test_background_property(self, user1, member1, team_chatroom):
            tm = TeamMessageFactory(chatroom=team_chatroom, user=user1, member=member1)

            assert tm.background == member1.background

            member1.delete()
            tm.refresh_from_db()

            assert tm.member is None
            assert tm.background == '0xff45474D'

            user1.delete()
            tm.refresh_from_db()

            assert tm.user is None
            assert tm.background == ''

            tm_not_msg = TeamMessageFactory(is_msg=False)

            assert tm_not_msg.background == ''

        def test_position_property(self, user1, member1, team_chatroom):
            tm = TeamMessageFactory(chatroom=team_chatroom, user=user1, member=member1)

            assert tm.position == member1.position.name

            member1.delete()
            tm.refresh_from_db()

            assert tm.member is None
            assert tm.position == ''

            user1.delete()
            tm.refresh_from_db()

            assert tm.user is None
            assert tm.position == ''

            tm_not_msg = TeamMessageFactory(is_msg=False)

            assert tm_not_msg.position == ''


@pytest.mark.django_db
class TestInquiryChatModels():
    def test_room_and_participant_creation(self, inquiry_chatroom):
        assert inquiry_chatroom.participants.count() == 2
        assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=True).exists()
        assert InquiryChatParticipant.objects.filter(chatroom=inquiry_chatroom, is_inquirer=False).exists()

    def test_delete_inquiry_chatroom_on_user_and_team_deletion(self, user1, team2, inquiry_chatroom):
        assert InquiryChatRoom.objects.filter(pk=inquiry_chatroom.pk).exists()

        user1.delete()
        team2.delete()

        assert not InquiryChatRoom.objects.filter(pk=inquiry_chatroom.pk).exists()

    class TestInquiryChatRoomProperties():
        def test_inquirer_chatroom_name(self, user1, team2, inquiry_chatroom):
            assert inquiry_chatroom.inquirer_chatroom_name == team2.name

            team2.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.inquirer_chatroom_name == '(알 수 없음)'

        def test_responsder_chatroom_name(self, user1, team2, inquiry_chatroom):
            assert inquiry_chatroom.team_chatroom_name == f'{team2.name} > {user1.name}'

            team2.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.team_chatroom_name == f'(알 수 없음) > {user1.name}'

        def test_inquirer_avatar(self, user1, inquiry_chatroom):
            assert inquiry_chatroom.inquirer_avatar == user1.avatar.url

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.inquirer_avatar == default_storage.url('users/default.png')

        def test_team_image(self, team2, inquiry_chatroom):
            assert inquiry_chatroom.team_image == team2.image.url

            team2.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.team_image == default_storage.url('teams/default.png')

        def test_inquirer_background(self, user1, inquiry_chatroom):
            assert inquiry_chatroom.inquirer_background == user1.background.url

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.inquirer_background == ''

        def test_responder(self, team2, inquiry_chatroom):
            assert inquiry_chatroom.responder is inquiry_chatroom.responder

            team2.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.responder is None

        def test_team_name(self, team2, inquiry_chatroom):
            assert inquiry_chatroom.team_name == team2.name

            team2.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.team_name == '(알 수 없음)'

        def test_inquirer_name(self, user1, inquiry_chatroom):
            assert inquiry_chatroom.inquirer_name == user1.name

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.inquirer_name == '(알 수 없음)'

        def test_responder_pk(self, team2, inquiry_chatroom):
            assert inquiry_chatroom.responder_pk == team2.responder.pk

            team2.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.responder_pk is None

        def test_inquirer_pk(self, user1, inquiry_chatroom):
            assert inquiry_chatroom.inquirer_pk == user1.pk

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.inquirer_pk is None

    class TestInquiryMessageProperties():
        def test_inquirer_msg_name(self, user1, inquiry_chatroom):
            inquirer_msg = InquiryMessageFactory(chatroom=inquiry_chatroom, sender=InquiryRoleType.INQUIRER)

            assert inquirer_msg.name == user1.name

            InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=True).delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.participants.all().count() == 1
            assert inquirer_msg.name == user1.name

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquirer_msg.name == '(알 수 없음)'

        def test_team_msg_name(self, team2, inquiry_chatroom):
            team_msg = InquiryMessageFactory(chatroom=inquiry_chatroom, sender=InquiryRoleType.TEAM)

            assert team_msg.name == team2.name

            InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=False).delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.participants.all().count() == 1
            assert team_msg.name == team2.name

            team2.delete()
            team_msg.refresh_from_db()

            assert team_msg.name == '(알 수 없음)'

        def test_inquirer_msg_avatar(self, user1, inquiry_chatroom):
            inquirer_msg = InquiryMessageFactory(chatroom=inquiry_chatroom, sender=InquiryRoleType.INQUIRER)

            assert inquirer_msg.avatar == user1.avatar.url

            InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=True).delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.participants.all().count() == 1
            assert inquirer_msg.avatar == user1.avatar.url

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquirer_msg.avatar == default_storage.url('avatars/default.png')

        def test_team_msg_avatar(self, team2, inquiry_chatroom):
            team_msg = InquiryMessageFactory(chatroom=inquiry_chatroom, sender=InquiryRoleType.TEAM)

            assert team_msg.avatar == team2.image.url

            InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=False).delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.participants.all().count() == 1
            assert team_msg.avatar == team2.image.url

            team2.delete()
            team_msg.refresh_from_db()

            assert team_msg.avatar == default_storage.url('teams/default.png')

        def test_inquirer_background(self, user1, inquiry_chatroom):
            inquirer_msg = InquiryMessageFactory(chatroom=inquiry_chatroom, sender=InquiryRoleType.INQUIRER)

            assert inquirer_msg.background == user1.background.url

            InquiryChatParticipant.objects.get(chatroom=inquiry_chatroom, is_inquirer=True).delete()
            inquiry_chatroom.refresh_from_db()

            assert inquiry_chatroom.participants.all().count() == 1
            assert inquirer_msg.background == user1.background.url

            user1.delete()
            inquiry_chatroom.refresh_from_db()

            assert inquirer_msg.background == ''

        
