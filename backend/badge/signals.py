from django.db.models.signals import pre_delete, post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction

from user.models import User, UserLikes, UserProfile
from team.models import Team, TeamMembers, TeamApplication
from post.models import TeamPost
from .models import *
from .utils import *

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
               before_level = badge.friendship_level
               if friend_cnt >= 50:
                    badge.friendship_level = 3
               elif friend_cnt >= 30:
                    badge.friendship_level = 2
               elif friend_cnt >= 5:
                    badge.friendship_level = 1
               if before_level != badge.friendship_level:
                    badge.friendship_change = True
                    send_level_badge_fcm(instance.pk, 'friendship', badge.friendship_level)
               badge.save()

@receiver(post_save, sender=TeamMembers)
def update_team_participance_level(sender, instance, created, **kwargs):
     if created:
          user = instance.user
          badge = user.badge
          if badge.team_participance_level < 3:
               before_level = badge.team_participance_level
               badge.team_participance_cnt += 1
               if before_level != badge.team_participance_level:
                    badge.team_participance_change = True
                    send_level_badge_fcm(user.pk, 'team_participance', badge.team_participance_level)
               badge.save()
               
@receiver(post_save, sender=TeamPost)
def update_team_post_level(sender, instance, created, **kwargs):
     if created:
          user = instance.writer.user
          badge = user.badge
          if badge.team_post_level < 3:
               before_level = badge.team_post_level
               team_post_cnt = TeamPost.objects.filter(writer__user=user).count()
               if team_post_cnt >= 30:
                    badge.team_post_level = 3
               elif team_post_cnt >= 10:
                    badge.team_post_level = 2
               elif team_post_cnt >= 5:
                    badge.team_post_level = 1
               if before_level != badge.team_post_level:
                    badge.team_post_change = True
                    send_level_badge_fcm(user.pk, 'team_post', badge.team_post_level)
               badge.save()

@receiver(post_save, sender=TeamMembers)
def update_recruit_level(sender, instance, created, **kwargs):
     if created:
          creator = instance.team.creator
          badge = creator.badge
          if badge.recruit_level < 3:
               before_level = badge.recruit_level
               badge.recruit_cnt += 1
               if before_level != badge.recruit_level:
                    badge.recruit_change = True
                    send_level_badge_fcm(creator.pk, 'recruit', badge.recruit_level)
               badge.save()

@receiver(post_save, sender=UserLikes)
def update_liked_level(sender, instance, created, **kwargs):
     liked_user = instance.to_user
     badge = liked_user.badge
     if badge.liked_level < 3:
          before_level = badge.liked_level
          liked_cnt = UserLikes.objects.filter(to_user=liked_user).count()
          if liked_cnt >= 50:
               badge.liked_level = 3
          elif liked_cnt >= 30:
               badge.liked_level = 2
          elif liked_cnt >= 10:
               badge.liked_level = 1
          if before_level != badge.liked_level:
               badge.liked_change = True
               send_level_badge_fcm(liked_user.pk, 'liked', badge.liked_level)
               
          badge.save()

@receiver(post_save, sender=TeamApplication)
def update_team_refusal_status(sender, instance, created, **kwargs):
     if not created:
          user = instance.applicant
          badge = user.badge
          if not badge.team_refusal_status and not instance.accepted:
               badge.team_refusal_status = True
               badge.team_refusal_change = True
               badge.save()
               send_status_badge_fcm(user.pk, 'team_refusal')

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
                    badge.user_profile_change = True
                    badge.save()
                    send_status_badge_fcm(instance.user.pk, 'user_profile')
                    


@receiver(post_save, sender=Team)
def update_team_leader_status(sender, instance, created, **kwargs):
     if created:
          user = instance.creator
          badge = user.badge
          if not badge.team_leader_status:
               badge.team_leader_status = True
               badge.team_leader_change = True
               badge.save()
               send_status_badge_fcm(user.pk, 'team_leader')