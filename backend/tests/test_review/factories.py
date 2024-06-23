import random

import factory
from faker import Faker
import pytest

from review.models import UserReview, UserReviewKeyword
from tests.test_user.factories import UserFactory

fake = Faker()


@pytest.mark.django_db
class UserReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserReview

    reviewer = factory.SubFactory(UserFactory)
    reviewee = factory.SubFactory(UserFactory)
    activity = random.randint(1, 6)
    star_rating = random.randint(0, 6)
    content = factory.Faker('text', max_nb_chars=300)

    @factory.post_generation
    def set_review_keywords(self, create, extracted, **kwargs):
        if create:
            keywords = UserReviewKeyword.objects.order_by('?')[:random.randint(1, 3)]
            self.keywords.set(keywords)


@pytest.mark.django_db
class UserReviewCommentFactory(factory.django.DjangoModelFactory):
    review = factory.SubFactory(UserReviewFactory)
    content = factory.Faker('text', max_nb_chars=200)