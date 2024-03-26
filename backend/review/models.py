from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from user.models import User

class ReviewKeywordType(models.IntegerChoices):
     POSITIVE = 1, 'Positive'
     NEGATIVE = 2, 'Negative'

class ActivityType(models.IntegerChoices):
     PROJECT = 1, '프로젝트'
     SUPPORTERS = 2, '서브터즈/공모전'
     CLUB = 3, '동아리/학회'
     STARTUP = 4, '창업'
     STUDY = 5, '스터디'
     
def validate_0_5_increment(value):
     if float(value) % 0.5 != 0:
          raise ValidationError("Star rating must be in 0.5 increments.")

class UserReviewKeyword(models.Model):
     content = models.TextField(default='', max_length=20)
     type = models.IntegerField(choices=ReviewKeywordType.choices)

     def __str__(self):
          return self.content

class UserReview(models.Model):
     id = models.AutoField(primary_key=True)
     reviewer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="written_reviews")
     reviewee = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="reviews")
     timestamp = models.DateTimeField(auto_now_add=True)
     activity = models.IntegerField(choices=ActivityType.choices)
     star_rating = models.DecimalField(
          max_digits=2,
          decimal_places=1,
          validators=[
               MinValueValidator(0),
               MaxValueValidator(5),
               validate_0_5_increment,
          ]
     )
     content = models.TextField(default='', max_length=300)
     keywords = models.ManyToManyField(
          UserReviewKeyword,
          related_name='users'
     )
     edited = models.BooleanField(default=False)
     
     class Meta:
          ordering = ["-timestamp"]
     
     def save(self, *args, **kwargs):
          is_new = self.pk is None
          if not is_new:
               self.edited = True
          super().save(*args, **kwargs)
          
class UserReviewComment(models.Model):
     id = models.AutoField(primary_key=True)
     review = models.OneToOneField(UserReview, on_delete=models.CASCADE, related_name='comment')
     timestamp = models.DateTimeField(auto_now_add=True)
     content = models.TextField(default='', blank=False, max_length=300)
     edited = models.BooleanField(default=False)
     
     def save(self, *args, **kwargs):
          is_new = self.pk is None
          if not is_new:
               self.edited = True
          super().save(*args, **kwargs)
          

