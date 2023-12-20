from rest_framework import serializers
from django.core.files.storage import default_storage
from django.db import transaction

from home.serializers import ImageBase64Field
from .models import *

class ArticleDetailSerializer(serializers.ModelSerializer):
     class Meta:
          model = Article
          fields = '__all__'

class ArticleCreateSerializer(serializers.ModelSerializer):
     image = ImageBase64Field()
     
     class Meta:
          model = Article
          fields = '__all__'
     
     @transaction.atomic 
     def create(self, validated_data):
          image = validated_data.pop('image', None)
          article = super().create(validated_data)

          # uploat image to S3, store image path in db
          image_path = f'articles/{article.pk}/main.png'
          default_storage.save(image_path, image)
          article.image = image_path
          article.save()
          
          return article

     def to_representation(self, instance):
          return ArticleDetailSerializer(instance).data
          