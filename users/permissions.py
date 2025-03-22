from rest_framework import permissions

class HasRole(permissions.BasePermission):
    def __init__(self, roles):
        self.roles = roles

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.roles