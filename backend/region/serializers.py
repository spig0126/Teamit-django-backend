from rest_framework import serializers

from .models import City, Province

class ProvinceSerializer(serializers.ModelSerializer):
     class Meta:
          model = Province
          fields = ['id', 'name']

class CitySerializer(serializers.ModelSerializer):
     class Meta:
          model = City
          fields = ['id', 'name']
          
class CityWithProvinceSerializer(serializers.ModelSerializer):
     province = ProvinceSerializer(read_only=True)
     
     class Meta:
          model = City
          fields = ['id', 'name', 'province']
     
class ProvinceWithCitiesSerializer(serializers.ModelSerializer):
     cities = serializers.SerializerMethodField()
     class Meta:
          model = Province
          fields = ['id', 'name', 'cities']
     
     def get_cities(self, instance):
          serializer = CitySerializer(instance.cities, many=True)
          return serializer.data
