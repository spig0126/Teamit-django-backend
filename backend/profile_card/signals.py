from django.db import transaction
from django.dispatch import Signal, receiver

from user.models import User
from .models import *

user_created = Signal()
user_updated = Signal()

@receiver(user_created)
def create_profile_card(sender, instance, **kwargs):
     with transaction.atomic():
          ProfileCard.objects.create(
               user = instance,
               interest = instance.main_interest,
               position = instance.main_position
          )

@receiver(user_updated)
def update_profile_card(sender, instance, **kwargs):
     with transaction.atomic():
          card = instance.profile_card
          if card.interest > instance.interests.count() - 1:
               card.interest = 0
          if card.position > instance.positions.count() - 1:
               card.position = 0
          card.save()