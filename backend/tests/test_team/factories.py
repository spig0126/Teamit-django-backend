from datetime import timedelta, date
import random

import pytest
import factory
from faker import Faker

from activity.models import Activity
from interest.models import Interest
from position.models import Position
from region.models import City
from team.models import Team, TeamMembers, TeamPositions, TeamApplication
from tests.test_user.factories import UserFactory

fake = Faker()


@pytest.mark.django_db
class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    creator = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Team{n}')
    short_pr = factory.Faker('text', max_nb_chars=50)
    keywords = '#성실 #꼼꼼 #끈기'
    activity = factory.LazyFunction(lambda: Activity.objects.order_by('?').first())
    interest = factory.LazyFunction(lambda: Interest.objects.order_by('?').first())
    meet_preference = factory.Faker('random_int', min=0, max=100)
    long_pr = factory.Faker('text')
    recruit_startdate = fake.date_between(start_date=date.fromisoformat('2024-01-01'), end_date=date.fromisoformat('2024-10-01')).strftime('%Y-%m-%d')
    recruit_enddate = factory.lazy_attribute(
        lambda o: fake.date_between(start_date=date.fromisoformat(o.recruit_startdate) + timedelta(days=7), end_date=date.fromisoformat('2024-12-31')).strftime('%Y-%m-%d'))
    active_startdate = factory.lazy_attribute(
        lambda o: fake.date_between(start_date=date.fromisoformat('2024-01-01'), end_date=date.fromisoformat('2024-12-01')).strftime('%Y-%m-%d'))
    active_enddate = factory.lazy_attribute(
        lambda o: fake.date_between(start_date=max(date.fromisoformat(o.active_startdate), date.fromisoformat(o.recruit_enddate)) + timedelta(days=30), end_date=date.fromisoformat('2025-12-31')).strftime('%Y-%m-%d'))

    @factory.post_generation
    def add_creator_as_member(self, create, extracted, **kwargs):
        if create:
            TeamMemberFactory(team=self, user=self.creator)

    @factory.post_generation
    def create_team_cities(self, create, extracted, **kwargs):
        if create:
            self.cities.add(City.objects.order_by('?').first())

    @factory.post_generation
    def create_team_positions(self, create, extracted, **kwargs):
        if create:
            for _ in range(random.randint(0, 5)):
                TeamPositionFactory(team=self)


@pytest.mark.django_db
class TeamMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamMembers

    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    position = factory.LazyFunction(lambda: Position.objects.order_by('?').first())
    background = '0xff' + fake.hex_color()[1:]
    custom_name = factory.Faker('text', max_nb_chars=10)


@pytest.mark.djano_db
class TeamPositionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamPositions

    team = factory.SubFactory(TeamFactory)
    position = factory.LazyFunction(lambda: Position.objects.order_by('?').first())
    pr = factory.Faker('sentence')
    cnt = factory.Faker('random_int', min=0, max=3000)


@pytest.mark.django_db
class TeamApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamApplication

    team = factory.SubFactory(TeamFactory)
    applicant = factory.SubFactory(UserFactory)
    position = factory.LazyFunction(lambda: Position.objects.order_by('?').first())
