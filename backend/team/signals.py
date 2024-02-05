from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import TeamPermission, TeamMembers
from user.models import User


@receiver(pre_delete, sender=User)
def update_team_permissions(sender, instance, **kwargs):
     team_permissions = TeamPermission.objects.filter(responder=instance)
     
     for permission in team_permissions:
          permission.responder = permission.team.creator
          permission.save()

     instance.delete()

@receiver(pre_delete, sender=TeamMembers)
def update_team_permissions(sender, instance, **kwargs):
     team_permissions = TeamPermission.objects.filter(responder=instance.user)
     
     for permission in team_permissions:
          permission.responder = permission.team.creator
          permission.save()

     instance.delete()