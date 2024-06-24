from django.db import models
from dateutil.relativedelta import *
from datetime import *
from django.conf import settings
from django.core.exceptions import ValidationError
from collections import Counter
from django.db.models import Avg

from region.models import Province, City
from position.models import Position
from interest.models import Interest
from activity.models import Activity


# Choices
class Sex(models.TextChoices):
    FEMALE = "F", "여자"
    MALE = "M", "남자"
    UNSPECIFIED = "U", "선택하지 않을래요"


class PriorityLevels(models.IntegerChoices):
    LOW = 2, 'Low'
    MEDIUM = 1, 'Medium'
    HIGH = 0, 'High'


# Models
class User(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.CharField(max_length=128, unique=True, default='')
    name = models.CharField(max_length=20, unique=True)
    interests = models.ManyToManyField(
        Interest,
        through='UserInterest',
        related_name="users"
    )
    positions = models.ManyToManyField(
        Position,
        through='UserPosition',
        related_name="users",
    )
    avatar = models.ImageField(upload_to='avatars/', default='avatars/1.png')
    background = models.ImageField(upload_to='backgrounds/', default='backgrounds/bg1.png')
    friends = models.ManyToManyField(
        'self',
        symmetrical=True
    )
    blocked_users = models.ManyToManyField(
        'self',
        symmetrical=False
    )
    blocked_teams = models.ManyToManyField(
        settings.TEAM_MODEL,
        related_name="blocked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def interest_names(self):
        return [str(interest) for interest in self.interests.all()]

    @property
    def position_names(self):
        return [str(position) for position in self.positions.all()]

    @property
    def city_names(self):
        try:
            return [str(city) for city in self.profile.cities.all()]
        except Exception:
            return []

    @property
    def activity_names(self):
        try:
            return [str(activity) for activity in self.profile.activities.all()]
        except Exception:
            return []

    @property
    def keywords(self):
        try:
            return self.profile.keywords
        except Exception:
            return ''

    @property
    def main_interest(self):
        return self.interests.get(userinterest__priority=PriorityLevels.HIGH)

    @property
    def main_position(self):
        return self.positions.get(userposition__priority=PriorityLevels.HIGH)

    @property
    def main_activity(self):
        return self.profile.activities.get(useractivity__priority=PriorityLevels.HIGH)

    @property
    def main_city(self):
        return self.profile.cities.get(usercity__priority=PriorityLevels.HIGH)

    @property
    def star_rating_average(self):
        if self.reviews.count() > 5:
            avg_star_rating = self.reviews.aggregate(avg_star_rating=Avg('star_rating'))['avg_star_rating']
            return round(avg_star_rating, 1)
        return None

    @property
    def review_keywords(self):
        from review.models import UserReviewKeyword
        keywords = [str(keyword) for keyword in UserReviewKeyword.objects.filter(reviews__reviewee=self)]
        c = Counter(keywords)
        common_keywords = list([keyword for keyword in c if c[keyword] > 1])
        uncommon_keywords = list([keyword for keyword in c if c[keyword] == 1])
        return {'common': common_keywords, 'uncommon': uncommon_keywords}


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')

    # 필수정보 (아래 항목들 + User의 positions, avatar, interests)
    birthdate = models.CharField(max_length=10, default="1900-01-01")
    sex = models.CharField(max_length=1, choices=Sex.choices, default=Sex.UNSPECIFIED)
    cities = models.ManyToManyField(
        City,
        through='UserCity',
        related_name="users"
    )
    activities = models.ManyToManyField(
        Activity,
        through='UserActivity',
        related_name="users"
    )
    short_pr = models.CharField(max_length=50, default='', blank=True)

    # 선택 정보
    education = models.CharField(default='', blank=True)
    keywords = models.CharField(default='', max_length=60, blank=True)
    tools = models.CharField(default='', max_length=70, blank=True)
    certificates = models.TextField(default='', max_length=100, blank=True)

    def __str__(self):
        return self.user.name

    @property
    def age(self):
        today = date.today()
        birthdate = date.fromisoformat(self.birthdate)
        age = relativedelta(today, birthdate)
        return age.years

    @property
    def region(self):
        p_name = Province.objects.get(id=self.province_id)
        c_name = City.objects.get(id=self.city_id)
        if c_name == "전체":
            return p_name + "권"
        return p_name + " " + c_name


class UserExternalLink(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='links')
    title = models.CharField(default='', max_length=20)
    url = models.URLField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.user_profile.links.count() > 5:
            raise ValidationError('A user profile can have a maximum of 5 links.')
        super().save(*args, **kwargs)


class UserExperience(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='experiences')
    image = models.ImageField(upload_to='users/', default='users/experience_default.png')
    title = models.CharField(max_length=20)
    start_end_date = models.CharField(max_length=23, default='')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    pinned = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.user_profile.experiences.count() > 10:
            raise ValidationError('A user profile can have a maximum of 10 experiences.')
        if self.pinned and self.user_profile.experiences.filter(pinned=True).count() > 2:
            raise ValidationError('A user profile can have a maximum of 2 pinned experiences.')
        super().save(*args, **kwargs)


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    accepted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            from notification.models import Notification
            from fcm_notification.utils import send_fcm_to_user

            # if receiver didn't block sender
            if self.from_user not in self.to_user.blocked_users.all():
                # send notification
                Notification.objects.create(
                    type="friend_request",
                    to_user=self.to_user,
                    related_id=self.id,
                )

                # send FCM notification
                title = '친구 요청 도착'
                body = f'{self.from_user} 님의 친구 요청이 도착했습니다.\n프로필을 확인해보세요.'
                data = {
                    "page": "user_notification"
                }
                send_fcm_to_user(self.to_user, title, body, data)


class UserLikes(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_by')


# ManyToMany field models
class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(choices=PriorityLevels.choices, default=PriorityLevels.HIGH)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.user.interests.count() > 3:
            raise ValidationError('A user can have a maximum of 3 interests.')
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['priority']


class UserPosition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(choices=PriorityLevels.choices, default=PriorityLevels.HIGH)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.user.positions.count() > 3:
            raise ValidationError('A user can have a maximum of 3 positions.')
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['priority']


class UserActivity(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(choices=PriorityLevels.choices, default=PriorityLevels.HIGH)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.user.activities.count() > 3:
            raise ValidationError('A user can have a maximum of 3 activities.')
        super().save(*args, **kwargs)


class UserCity(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(choices=PriorityLevels.choices, default=PriorityLevels.HIGH)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.user.cities.count() > 3:
            raise ValidationError('A user can have a maximum of 3 cities.')
        super().save(*args, **kwargs)


class Tool(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField()

    class Meta:
        managed = False
