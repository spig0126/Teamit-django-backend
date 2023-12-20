from rest_framework import serializers

from .models import City, Province

# field serializers
class CitiesField(serializers.Field):
     def to_internal_value(self, data):
        # Convert list of city names to list of city(city) instances
          try:
               city_instances = []
               for region_name in data:
                    province_name, city_name = region_name.strip().split(' ', 1)
                    province = Province.objects.get(name=province_name)
                    city_instances.append(City.objects.get(name=city_name, province=province))
               return city_instances
          except (City.DoesNotExist, Province.DoesNotExist):
               raise serializers.ValidationError("Invalid city name")
     
     def to_representation(self, value):
          return [city.province.name + ' ' + city.name for city in value]

class CityField(serializers.Field):
     def to_internal_value(self, data):
        # Convert city name to city instance
          try:
               province_name, city_name = data.strip().split(' ', 1)
               province = Province.objects.get(name=province_name)
               city_instance = City.objects.get(name=city_name, province=province)
               return city_instance
          except city.DoesNotExist:
               raise serializers.ValidationError("Invalid city name")
     
     def to_representation(self, value):
          return city.province.name + ' ' + city.name

# model serializers  
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
