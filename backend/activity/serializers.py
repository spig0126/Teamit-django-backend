from rest_framework import serializers

from .models import Activity

class ActivitySerializer(serializers.ModelSerializer):
     class Meta:
          model = Activity
          fields = ['id', 'name']
          lookup_field = 'name'

class ActivityAllSerializer(serializers.ModelSerializer):
     class meta:
          model = Activity
          fields = '__all__' 