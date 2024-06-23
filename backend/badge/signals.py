from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction

from review.models import UserReview
from user.models import UserLikes, UserProfile
from team.models import Team, TeamMembers, TeamApplication
from post.models import TeamPost
from .models import *
from .utils import *


@receiver(post_save, sender=User)
def create_badge_and_count_user(sender, instance, created, **kwargs):
    if created:
        with transaction.atomic():
            badge = Badge.objects.create(user=instance)
            user_cnt = UserCount.objects.first()
            user_cnt.cnt += 1
            user_cnt.save()
            if user_cnt.cnt < 1000:
                badge.early_user_status = True
                badge.early_user_change = True
                badge.save()


@receiver(m2m_changed, sender=User.friends.through)
def update_friendship_level(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        badge = instance.badge
        if badge.friendship_level < 3:
            friend_cnt = instance.friends.count()
            before_level = badge.friendship_level
            if friend_cnt >= 50:
                badge.friendship_level = BadgeLevels.LEVEL_THREE
            elif friend_cnt >= 30:
                badge.friendship_level = BadgeLevels.LEVEL_TWO
            elif friend_cnt >= 5:
                badge.friendship_level = BadgeLevels.LEVEL_ONE
            if before_level != badge.friendship_level:
                badge.friendship_change = True
                send_level_badge_fcm(instance.pk, 'friendship', badge.friendship_level)
            badge.save()


@receiver(post_save, sender=TeamMembers)
def update_team_participance_level(sender, instance, created, **kwargs):
    if created:
        return
    user = instance.user
    badge = user.badge
    if user == instance.team.creator:
        return
    if badge.team_participance_level >= 3:
        return
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

        if creator == instance.user:
            return
        if badge.recruit_level >= 3:
            return
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
    if badge.liked_level >= 3:
        return
    before_level = badge.liked_level
    liked_cnt = UserLikes.objects.filter(to_user=liked_user).count()
    if liked_cnt >= 50:
        badge.liked_level = BadgeLevels.LEVEL_THREE
    elif liked_cnt >= 30:
        badge.liked_level = BadgeLevels.LEVEL_TWO
    elif liked_cnt >= 10:
        badge.liked_level = BadgeLevels.LEVEL_ONE
    if before_level != badge.liked_level:
        badge.liked_change = True
        send_level_badge_fcm(liked_user.pk, 'liked', badge.liked_level)
        badge.save()


@receiver(post_save, sender=UserReview)
def update_user_review_level(sender, instance, created, **kwargs):
    reviewer = instance.reviewer
    badge = reviewer.badge
    if not created:
        return
    if badge.user_review_level >= 3:
        return
    before_level = badge.user_review_level
    badge.user_review_cnt += 1
    if before_level != badge.user_review_level:
        badge.user_review_change = True
        send_level_badge_fcm(reviewer.pk, 'user_review', badge.user_review_level)
    badge.save()


@receiver(post_save, sender=TeamApplication)
def update_team_refusal_status(sender, instance, created, **kwargs):
    if created:
        return
    user = instance.applicant
    badge = user.badge
    if badge.team_refusal_status or instance.accepted:
        return
    badge.team_refusal_status = True
    badge.team_refusal_change = True
    badge.save()
    send_status_badge_fcm(user.pk, 'team_refusal')


@receiver(post_save, sender=UserProfile)
def update_user_profile_status(sender, instance, created, **kwargs):
    if created:
        return
    badge = instance.user.badge
    if badge.user_profile_status:
        return
    str_fields_to_check = [
        instance.education,
        instance.keywords,
        instance.tools,
        instance.certificates,
    ]
    related_fields_to_check = [
        instance.experiences,
        instance.links
    ]
    if any(field == '' for field in str_fields_to_check) or \
            any(not field.count() for field in related_fields_to_check):
        return
    badge.user_profile_status = True
    badge.user_profile_change = True
    badge.save()
    send_status_badge_fcm(instance.user.pk, 'user_profile')


@receiver(post_save, sender=Team)
def update_team_leader_status(sender, instance, created, **kwargs):
    if not created:
        return
    user = instance.creator
    badge = user.badge
    if badge.team_leader_status:
        return
    badge.team_leader_status = True
    badge.team_leader_change = True
    badge.save()
    send_status_badge_fcm(user.pk, 'team_leader')
