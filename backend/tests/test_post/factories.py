import factory

from post.models import TeamPost, TeamPostComment
from tests.test_team.factories import TeamMemberFactory, TeamFactory


class TeamPostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamPost

    writer = factory.SubFactory(TeamMemberFactory)
    post_to = factory.SubFactory(TeamFactory)
    content = factory.Faker('text')


class TeamPostComment(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamPostComment

    writer = factory.SubFactory(TeamMemberFactory)
    comment_to = factory.SubFactory(TeamPostFactory)
    content = factory.Faker('text')