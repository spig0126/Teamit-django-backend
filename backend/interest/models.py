from django.db import models


class CategoryType(models.IntegerChoices):
    IT = 1, 'IT related'
    MEDIA = 2, 'media related'
    LEISURE = 3, 'leiure related'
    BEAUTY = 4, 'beatuy related'
    ENVIRONMENT = 5, 'environment related'
    OTHER = 0, 'other related'


class Interest(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=10, unique=True)
    category = models.PositiveSmallIntegerField(choices=CategoryType.choices, default=0)

    def __str__(self):
        return self.name
