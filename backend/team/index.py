from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

from .models import Team

@register(Team)
class TeamIndex(AlgoliaIndex):
    fields = ('name', 'interest', 'position_names', 'activity', 'city_names', 'keywords')
    settings = {'searchableAttributes': ['name', 'interest', 'position_names', 'activity', 'city_names', 'keywords']}
    index_name = 'team_index'