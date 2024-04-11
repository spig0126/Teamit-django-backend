from rest_framework import serializers

from .models import Position

# field serializers
class PositionsField(serializers.Field):
     def to_internal_value(self, data):
          # Convert list of position names to list of position instances
          try:
               position_instances = []
               for position_name in data:
                    position_instances.append(Position.objects.get(name=position_name))
               return position_instances
          except Position.DoesNotExist:
               raise serializers.ValidationError("Invalid position name")
     
     def to_representation(self, value):
          return [position.name for position in value]

class PositionField(serializers.Field):
     def to_internal_value(self, data):
          # Convert position name to position instance
          try:
               position = Position.objects.get(name=data)
               return position
          except Position.DoesNotExist:
               raise serializers.ValidationError("Invalid position ID")
     
     def to_representation(self, value):
          return value.name

# model serializers
class PositionSerializer(serializers.ModelSerializer):
     class Meta:
          model = Position
          fields = ['id', 'name']

class PositionAllSerializer(serializers.ModelSerializer):
     class Meta:
          model = Position
          fields = "__all__"
