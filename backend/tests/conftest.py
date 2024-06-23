import pytest
from algoliasearch_django import AlgoliaIndex
from django.db import connection


@pytest.fixture(autouse=True)
def disable_algolia_indexing(mocker):
    mocker.patch.object(AlgoliaIndex, 'save_record')
    mocker.patch.object(AlgoliaIndex, 'delete_record')
    mocker.patch.object(AlgoliaIndex, 'update_records')

