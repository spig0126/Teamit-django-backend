from django.apps import AppConfig
from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register

class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
    
    # def ready(self):
    #     from .models import User
    #     from .index import UserIndex  # Replace with your actual index

    #     # Register the Algolia index
    #     UserIndex.register()
