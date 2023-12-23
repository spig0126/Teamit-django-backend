from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from .models import User

@register(User)
class UserIndex(AlgoliaIndex):
    fields = ('name', 'interest_names', 'position_names', 'activity_names', 'city_names', 'keywords')
    settings = {'searchableAttributes': ['name', 'interest_names', 'position_names', 'activity_names', 'city_names', 'keywords']}
    index_name = 'user_index'