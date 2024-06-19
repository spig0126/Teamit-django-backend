from rest_framework import serializers

from .models import *
from user.serializers import *


class UserReviewCommentCreateUpdateSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(slug_field='pk', queryset=UserReview.objects.all(), required=False)

    class Meta:
        model = UserReviewComment
        fields = [
            'review',
            'content'
        ]

    def to_representation(self, instance):
        return UserReviewCommentDetailSerializer(instance).data


class UserReviewCommentDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = UserReviewComment
        fields = '__all__'


class UserReviewCreateUpdateSerializer(serializers.ModelSerializer):
    reviewee = serializers.SlugRelatedField(slug_field='name', queryset=User.objects.all())
    activity = serializers.SlugRelatedField(slug_field='name', queryset=Activity.objects.all())
    star_rating = serializers.DecimalField(max_digits=2, decimal_places=1)
    keywords = serializers.SlugRelatedField(slug_field='content', many=True, queryset=UserReviewKeyword.objects.all(),
                                            required=False)

    class Meta:
        model = UserReview
        fields = [
            'reviewee',
            'activity',
            'star_rating',
            'content',
            'keywords',
        ]

    def to_representation(self, instance):
        return UserReviewDetailSerializer(instance).data


class UserReviewDetailSerializer(serializers.ModelSerializer):
    reviewer = UserMinimalWithAvatarBackgroundDetailSerializer()
    activity = serializers.StringRelatedField()
    keywords = serializers.StringRelatedField(many=True)
    comment = UserReviewCommentDetailSerializer()

    class Meta:
        model = UserReview
        fields = [
            'id',
            'reviewer',
            'timestamp',
            'activity',
            'star_rating',
            'content',
            'keywords',
            'comment',
            'edited'
        ]
