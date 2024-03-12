from django.db.models.signals import pre_delete, post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count, Sum

from user.models import User, UserLikes, UserProfile
from team.models import Team, TeamMembers, TeamApplication
from post.models import TeamPost
from .models import *

@receiver(post_save, sender=User)
def create_badge(sender, instance, created, **kwargs):
     if created:
          with transaction.atomic():
               Badge.objects.create(user=instance)

@receiver(m2m_changed, sender=User.friends.through)
def update_friendship_level(sender, instance, action, pk_set, **kwargs):
     if action == 'post_add':
          badge = instance.badge
          if badge.friendship_level < 3:
               friend_cnt = instance.friends.count()
               if friend_cnt >= 50:
                    badge.friendship_level = 3
               elif friend_cnt >= 30:
                    badge.friendship_level = 2
               elif friend_cnt >= 5:
                    badge.friendship_level = 1
               badge.save()

@receiver(post_save, sender=TeamMembers)
def update_team_participance_level(sender, instance, created, **kwargs):
     if created:
          user = instance.user
          badge = user.badge
          if badge.team_participance_level < 3:
               badge.team_participance_cnt += 1
               badge.save()
               
@receiver(post_save, sender=TeamPost)
def update_team_post_level(sender, instance, created, **kwargs):
     if created:
          user = instance.writer.user
          badge = user.badge
          if badge.team_post_level < 3:
               team_post_cnt = TeamPost.objects.filter(writer__user=user).count()
               if team_post_cnt >= 30:
                    badge.team_post_level = 3
               elif team_post_cnt >= 10:
                    badge.team_post_level = 2
               elif team_post_cnt >= 5:
                    badge.team_post_level = 1
               badge.save()

@receiver(post_save, sender=TeamMembers)
def update_recruit_level(sender, instance, created, **kwargs):
     if created:
          creator = instance.team.creator
          badge = creator.badge
          if badge.recruit_level < 3:
               badge.recruit_cnt += 1
               badge.save()

@receiver(post_save, sender=UserLikes)
def update_liked_level(sender, instance, created, **kwargs):
     liked_user = instance.to_user
     badge = liked_user.badge
     if badge.liked_level < 3:
          liked_cnt = UserLikes.objects.filter(to_user=liked_user).count()
          if liked_cnt >= 50:
               badge.liked_level = 3
          elif liked_cnt >= 30:
               badge.liked_level = 2
          elif liked_cnt >= 10:
               badge.liked_level = 1
          badge.save()

@receiver(post_save, sender=TeamApplication)
def update_team_refusal_status(sender, instance, created, **kwargs):
     if not created:
          user = instance.applicant
          badge = user.badge
          if not badge.team_refusal_status and not instance.accepted:
               badge.team_refusal_status = True
               badge.save()

@receiver(post_save, sender=UserProfile)
def update_user_profile_status(sender, instance, created, **kwargs):
     if not created:
          badge = instance.user.badge
          if not badge.user_profile_status:
               fields_to_check = [
                    instance.education,
                    instance.keywords,
                    instance.tools,
                    instance.experiences,
                    instance.certificates,
                    instance.links
               ]
               if not any(field == '' for field in fields_to_check):
                    badge.user_profile_status = True
                    badge.save()


@receiver(post_save, sender=Team)
def update_team_leader_status(sender, instance, created, **kwargs):
     if created:
          user = instance.creator
          badge = user.badge
          if not badge.team_leader_status:
               badge.team_leader_status = True
               badge.save()