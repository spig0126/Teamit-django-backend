from algoliasearch_django import algolia_engine

def get_client():
     return algolia_engine.client

def get_index(index_name='user_index'):
     client = get_client()
     index = client.init_index(index_name)
     return index

def refresh_user_index():
    users = User.objects.all()

    # Convert User objects to dictionaries suitable for indexing
    records = [{'objectID': str(user.pk), 'name': user.name, 'other_fields': user.other_fields} for user in users]

    # Push the data to Algolia to update the index
    index.save_objects(records)
def perform_search(query, **kwargs):
     index = get_index()
     results = index.search(query)
     return results