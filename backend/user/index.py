from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from user.models import User


@register(User)
class UserIndex(AlgoliaIndex):
    fields = ('pk', 'name', 'interest_names', 'position_names', 'activity_names', 'city_names', 'keywords')
    settings = {
        'searchableAttributes': [
            'name',
            'interest_names',
            'position_names',
            'activity_names',
            'city_names',
            'keywords'
        ],
        'attributesForFaceting': [
            'interest_names',
            'position_names',
            'city_names',
            'activity_names'
        ]
    }
    index_name = 'user_index'
    get_object_id = 'pk'
