from django.db import models


class Article(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=30, default='')
    image = models.ImageField(upload_to='articles/')
    writer = models.CharField(max_length=10, default='글쓴이')
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True)


class EventArticle(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=30, default='')
    subtitle = models.CharField(default='')
    image = models.ImageField(upload_to='event_articles/')
    background_color = models.CharField(max_length=10, default='0xffEEE7F7')
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = 'created_at'
