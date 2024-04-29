from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.db import transaction

from .models import UserExperience

@receiver(pre_delete, sender=UserExperience)
def delete_experience_S3_image(sender, instance, **kwargs):
     with transaction.atomic():
          default_image = instance._meta.get_field('image').get_default()
          if instance.image is not default_image:
               instance.image.delete(save=False)