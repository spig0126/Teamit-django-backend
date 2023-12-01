from rest_framework import serializers

from .models import Interest

class InterestSerializer(serializers.ModelSerializer):
     class Meta:
          model = Interest
          fields = ['id', 'name']

class InterestAllSerializer(serializers.ModelSerializer):
     class meta:
          model = Interest
          fields = '__all__' 