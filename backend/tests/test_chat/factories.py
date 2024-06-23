import factory
from faker import Faker

from chat.models import PrivateChatRoom, PrivateChatParticipant, PrivateMessage, TeamChatRoom, TeamChatParticipant, \
    TeamMessage, InquiryChatRoom, InquiryChatParticipant, InquiryMessage, InquiryRoleType
from tests.test_team.factories import TeamMemberFactory, TeamFactory
from tests.test_user.factories import UserFactory

fake = Faker()


class PrivateChatRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PrivateChatRoom

    @factory.post_generation
    def add_participants(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                PrivateChatParticipantFactory(chatroom=self, user=user)
        else:
            PrivateChatParticipantFactory(chatroom=self)
            PrivateChatParticipantFactory(chatroom=self)


class PrivateChatParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PrivateChatParticipant

    chatroom = factory.SubFactory(PrivateChatRoomFactory)
    user = factory.SubFactory(UserFactory)


class PrivateMessage(factory.django.DjangoModelFactory):
    class Meta:
        model = PrivateMessage

    chatroom = factory.SubFactory(PrivateChatRoomFactory)
    sender = factory.SubFactory(UserFactory)
    content = factory.Faker('test', max_nb_chars=255)


class InquiryChatRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InquiryChatRoom

    inquirer = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)


class InquiryChatParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InquiryChatParticipant

    chatroom = factory.SubFactory(InquiryChatRoomFactory)
    is_inquirer = factory.Faker('boolean')


class InquiryMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InquiryMessage

    chatroom = factory.SubFactory(InquiryChatRoomFactory)
    sender = factory.LazyFunction(lambda: fake.random_element(InquiryRoleType.values))
    content = factory.Faker('text', max_nb_chars=255)


class TeamChatRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamChatRoom

    team = factory.SubFactory(TeamFactory)
    name = factory.Sequence(lambda n: f'Team{n}')
    background = '0xff' + fake.hex_color()[1:]

    @factory.post_generation
    def add_participants(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user, member in extracted:
                TeamChatParticipantFactory(chatroom=self, user=user, member=member)
        else:
            TeamChatParticipantFactory(chatroom=self)
            TeamChatParticipantFactory(chatroom=self)


class TeamChatParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamChatParticipant

    chatroom = factory.SubFactory(TeamChatRoomFactory)
    member = factory.SubFactory(TeamMemberFactory)
    user = factory.SubFactory(UserFactory)


class TeamMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamMessage

    chatroom = factory.SubFactory(TeamChatRoomFactory)
    member = factory.SubFactory(TeamMemberFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.Faker('text', max_nb_chars=255)
    is_msg = factory.LazyFunction(lambda: True)