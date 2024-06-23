from rest_framework import permissions


class CanEditUser(permissions.BasePermission):
    message = "user not allowed to edit this user"

    def has_permission(self, request, view):
        if request.method in ('PUT', 'PATCH', 'DELETE'):
            user_name = view.kwargs.get('name')
            return request.user.name == user_name
        return True  # Allow GET requests
