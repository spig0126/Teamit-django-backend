import random

import pytest
from datetime import datetime, date, timedelta
import factory
from faker import Faker

from activity.models import Activity
from interest.models import Interest
from position.models import Position
from region.models import City
from user.models import User, UserProfile, UserExperience, UserInterest, UserPosition, UserActivity, UserCity, \
    UserExternalLink

fake = Faker()


@pytest.fixture(autouse=True)
def reset_faker_unique():
    fake.unique.clear()


@pytest.mark.django_db
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    name = factory.Sequence(lambda n: f'User{n}')
    uid = factory.LazyFunction(lambda: fake.uuid4()[:100])

    @factory.post_generation
    def create_user_profile(self, create, extracted, **kwargs):
        if create:
            UserProfileFactory(user=self)

    @factory.post_generation
    def create_user_interests_positions(self, create, extracted, **kwargs):
        if create:
            for i in range(random.randint(1, 3)):
                UserInterestFactory(user=self, priority=i)
                UserPositionFactory(user=self, priority=i)


@pytest.mark.django_db
class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    sex = factory.Faker('random_element', elements=('M', 'F', 'U'))
    short_pr = factory.Faker('text', max_nb_chars=50)
    education = '게더어스학교'
    keywords = '#성실 #꼼꼼 #끈기'
    tools = '#Django #Github'
    certificates = '#TOEIC #TOEFL'

    @factory.post_generation
    def create_user_cities(self, create, extracted, **kwargs):
        if create:
            for i in range(random.randint(1, 3)):
                UserCityFactory(user=self, priority=i)
                UserActivityFactory(user=self, priority=i)


@pytest.mark.django_db
class UserExperienceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserExperience

    user_profile = factory.SubFactory(UserProfileFactory)
    title = factory.Faker('text', max_nb_chars=20)
    activity = factory.LazyFunction(lambda: Activity.objects.order_by('?').first())

    @factory.lazy_attribute
    def start_end_date(self):
        start_date = fake.date_between(start_date=date.fromisoformat('2023-01-01'),
                                              end_date=date.fromisoformat('2023-10-01')).strftime('%Y-%m-%d')
        end_date =  fake.date_between(start_date=date.fromisoformat('2023-11-01'),
                                              end_date=date.fromisoformat('2024-05-01')).strftime('%Y-%m-%d')
        return f"{start_date} - {end_date}"


class UserExternalLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserExternalLink

    user_profile = factory.SubFactory(UserProfileFactory)
    title = factory.Faker('text', max_nb_chars=20)
    url = factory.Faker('url')


class UserInterestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserInterest

    user = factory.SubFactory(UserFactory)
    interest = factory.LazyFunction(lambda: Interest.objects.order_by('?').first())


class UserPositionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserPosition

    user = factory.SubFactory(UserFactory)
    position = factory.LazyFunction(lambda: Position.objects.order_by('?').first())


class UserActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserActivity

    user = factory.SubFactory(UserFactory)
    activity = factory.LazyFunction(lambda: Activity.objects.order_by('?').first())


class UserCityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserCity

    user = factory.SubFactory(UserFactory)
    city = factory.LazyFunction(lambda: City.objects.order_by('?').first())
