from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User 
from .index import UserIndex

@receiver(post_save, sender=User)
def update_user_index(sender, instance, **kwargs):
     UserIndex.save_record(instance)

          
@receiver(post_delete, sender=User)
def delete_user_index(sender, instance, **kwargs):
     UserIndex.delete_record(instance)