from rest_framework import serializers

from .models import Interest


# field serializers
class InterestsField(serializers.Field):
    def to_internal_value(self, data):
        # Convert list of interest names to list of interest instances
        try:
            interest_instances = []
            for interest_name in data:
                interest_instances.append(Interest.objects.get(name=interest_name))
            return interest_instances
        except Interest.DoesNotExist:
            raise serializers.ValidationError("Invalid interest name")

    def to_representation(self, value):
        return [interest.name for interest in value]


class InterestField(serializers.Field):
    def to_internal_value(self, data):
        # Convert interest name to interest instance
        try:
            interest_instance = Interest.objects.get(name=data)
            return interest_instance
        except Interest.DoesNotExist:
            raise serializers.ValidationError("Invalid interest name")

    def to_representation(self, value):
        return value.name


# model serializers
class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']


class InterestAllSerializer(serializers.ModelSerializer):
    class meta:
        model = Interest
        fields = '__all__'
