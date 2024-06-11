from django.db import models
from django.core.files.storage import default_storage

from user.models import User


class BadgeLevels(models.IntegerChoices):
    LEVEL_DEFAULT = 0, 'Level default'
    LEVEL_ONE = 1, 'Level 1'
    LEVEL_TWO = 2, 'Level 2'
    LEVEL_THREE = 3, 'Level 3'


class BadgeType(models.IntegerChoices):
    ATTENDANCE = 0, 'attendance'
    FRIENDSHIP = 1, 'friendship'
    TEAM_PARTICIPANCE = 2, 'team_participance'
    TEAM_POST = 3, 'team_post'
    LIKED = 4, 'liked'
    RECRUIT = 5, 'recruit'
    TEAM_REFUSAL = 6, 'team_refusal'
    USER_PROFILE = 7, 'user_profile'
    TEAM_LEADER = 8, 'team_leader'
    SHARED_PROFILE = 9, 'shared_profile'
    EARLY_USER = 10, 'early_user'


class Badge(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='badge')
    attendance_cnt = models.PositiveIntegerField(default=0)
    attendance_change = models.BooleanField(default=False)
    friendship_level = models.IntegerField(choices=BadgeLevels.choices, default=BadgeLevels.LEVEL_DEFAULT)
    friendship_change = models.BooleanField(default=False)
    team_participance_cnt = models.PositiveIntegerField(default=0)
    team_participance_change = models.BooleanField(default=False)
    team_post_level = models.IntegerField(choices=BadgeLevels.choices, default=BadgeLevels.LEVEL_DEFAULT)
    team_post_change = models.BooleanField(default=False)
    liked_level = models.IntegerField(choices=BadgeLevels.choices, default=BadgeLevels.LEVEL_DEFAULT)
    liked_change = models.BooleanField(default=False)
    recruit_cnt = models.PositiveIntegerField(default=0)
    recruit_change = models.BooleanField(default=False)
    team_refusal_status = models.BooleanField(default=False)
    team_refusal_change = models.BooleanField(default=False)
    user_profile_status = models.BooleanField(default=False)
    user_profile_change = models.BooleanField(default=False)
    team_leader_status = models.BooleanField(default=False)
    team_leader_change = models.BooleanField(default=False)
    shared_profile_status = models.BooleanField(default=False)
    shared_profile_change = models.BooleanField(default=False)
    early_user_status = models.BooleanField(default=False)
    early_user_change = models.BooleanField(default=False)

    @property
    def recruit_level(self):
        if self.recruit_cnt >= 30:
            return BadgeLevels.LEVEL_THREE
        elif self.recruit_cnt >= 15:
            return BadgeLevels.LEVEL_TWO
        elif self.recruit_cnt >= 5:
            return BadgeLevels.LEVEL_ONE
        else:
            return BadgeLevels.LEVEL_DEFAULT

    @property
    def team_participance_level(self):
        if self.team_participance_cnt >= 5:
            return BadgeLevels.LEVEL_THREE
        elif self.team_participance_cnt >= 3:
            return BadgeLevels.LEVEL_TWO
        elif self.team_participance_cnt >= 1:
            return BadgeLevels.LEVEL_ONE
        else:
            return BadgeLevels.LEVEL_DEFAULT

    @property
    def attendance_level(self):
        if self.attendance_cnt >= 25:
            return BadgeLevels.LEVEL_THREE
        elif self.attendance_cnt >= 14:
            return BadgeLevels.LEVEL_TWO
        elif self.attendance_cnt >= 5:
            return BadgeLevels.LEVEL_ONE
        else:
            return BadgeLevels.LEVEL_DEFAULT

    @property
    def latest_badge_images(self):
        badge_types = [choice[1] for choice in BadgeType.choices]
        img = []
        for badge_type in badge_types:
            try:
                badge_level = getattr(self, badge_type + '_level')
            except AttributeError:
                try:
                    badge_level = getattr(self, badge_type + '_status')
                except AttributeError:
                    badge_level = getattr(self.__class__, badge_type + '_level').__get__(self)
            if type(badge_level) is bool and badge_level:
                img.append(default_storage.url(f'badges/{badge_type}.png'))
            elif badge_level:
                img.append(default_storage.url(f'badges/{badge_type}/{badge_level}.png'))
        return img


class UserCount(models.Model):
    cnt = models.PositiveIntegerField(default=0)
