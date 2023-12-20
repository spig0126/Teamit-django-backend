from rest_framework import serializers

from .models import Activity

# field serializers
class AcitivitiesField(serializers.Field):
     def to_internal_value(self, data):
        # Convert list of activity names to list of activity instances
          try:
               activity_instances = []
               for activity_name in data:
                    activity_instances.append(Activity.objects.get(name=activity_name))
               return activity_instances
          except Activity.DoesNotExist:
               raise serializers.ValidationError("Invalid activity name")
     
     def to_representation(self, value):
          return [activity.name for activity in value]

class ActivityField(serializers.Field):
     def to_internal_value(self, data):
        # Convert activity name to activity instance
          try:
               activity_instance = Activity.objects.get(name=data)
               return activity_instance
          except Activity.DoesNotExist:
               raise serializers.ValidationError("Invalid activity name")
     
     def to_representation(self, value):
          return value.name

# model serializers  
class ActivitySerializer(serializers.ModelSerializer):
     class Meta:
          model = Activity
          fields = ['id', 'name']
          lookup_field = 'name'

class ActivityAllSerializer(serializers.ModelSerializer):
     class meta:
          model = Activity
          fields = '__all__' 