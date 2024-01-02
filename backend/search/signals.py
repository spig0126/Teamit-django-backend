from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .index import *
@receiver(post_save, sender=User)
def update_user_index(sender, instance, **kwargs):
    # Update or create a record in Algolia index
    UserIndex.save_record(instance)

@receiver(post_delete, sender=User)
def delete_user_index(sender, instance, **kwargs):
    # Delete the record from Algolia index
    UserIndex.delete_record(instance)