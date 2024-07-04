from algoliasearch_django import algolia_engine


def get_client():
    return algolia_engine.client


def get_index(index_name='team_index'):
    client = get_client()
    index = client.init_index(index_name)
    return index


def perform_search(query, page, **kwargs):
    index = get_index()
    results = index.search(query, {'page': page})
    return results
