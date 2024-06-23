from rest_framework import permissions
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException
from rest_framework import status

from team.models import Team
from user.models import User


class ReviewerRevieweeSameException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'reivewer and reviewee cannot be the same'


class IsEligibleForReviewer(permissions.BasePermission):
    message = "permission denied because user is not eligible for reviewer"

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        reviewer = request.user
        reviewee = get_object_or_404(User, name=request.data.get('reviewee', None))
        if reviewer == reviewee:
            raise ReviewerRevieweeSameException()
        is_friend = reviewer.friends.filter(pk=reviewee.pk).exists()
        is_team_member = Team.objects.filter(members=reviewer).filter(members=reviewee).exists()
        is_new_reviewer = not reviewee.reviews.filter(reviewer=reviewer.pk).exists()
        return is_new_reviewer and (is_friend or is_team_member)


class IsReviewee(permissions.BasePermission):
    message = "permission denied because only reviewee can comment review"

    def has_permission(self, request, view):
        reviewee = request.user
        review = view.review
        return review.reviewee == reviewee


class IsReviewer(permissions.BasePermission):
    message = "permission denied because user is not reviewer"

    def has_permission(self, request, view):
        reviewer = request.user
        review = view.review
        return review.reviewer == reviewer
