from django.db import models

class Article(models.Model):
     id = models.AutoField(primary_key=True)
     title = models.CharField(max_length=30, default='')
     image = models.ImageField(upload_to='articles/')
     writer = models.CharField(max_length=10, default='글쓴이')
     link = models.URLField()
     created_at = models.DateTimeField(auto_now_add=True, blank=True)
     