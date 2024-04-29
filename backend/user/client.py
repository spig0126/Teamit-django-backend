from algoliasearch_django import algolia_engine

def get_client():
     return algolia_engine.client

def get_index(index_name='user_index'):
     client = get_client()
     index = client.init_index(index_name)
     return index

def perform_search(query, **kwargs):
     index = get_index()
     results = index.search(query)
     return results['hits']

def perform_filtered_search(filter_expression, **kwargs):
     index = get_index()
     results = index.search('', {'filters': filter_expression})
     return results['hits']