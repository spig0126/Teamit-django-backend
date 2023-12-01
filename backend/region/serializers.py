from rest_framework import serializers

from .models import City, Province

class ProvinceSerializer(serializers.ModelSerializer):
     class Meta:
          model = Province
          fields = ['id', 'name']

class CitySerializer(serializers.ModelSerializer):
     province = ProvinceSerializer(read_only=True)
     
     class Meta:
          model = City
          fields = ['id', 'name', 'province']