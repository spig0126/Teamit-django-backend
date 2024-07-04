from algoliasearch_django import algolia_engine

index_name = {
    'private': 'private_chat_participant_index',
    'team': 'team_chat_participant_index',
    'inquiry': 'inquiry_chatroom_index'
}


def get_client():
    return algolia_engine.client


def get_index(index_name):
    client = get_client()
    index = client.init_index(index_name)
    return index


def perform_search(query, chat_type, filter_expression, page, **kwargs):
    index = get_index(index_name[chat_type])
    results = index.search(query, {'page': page, 'filters': filter_expression, 'attributesToHighlight': []})
    return [{key: value for key, value in hit.items() if key != 'objectID'} for hit in results['hits']]
