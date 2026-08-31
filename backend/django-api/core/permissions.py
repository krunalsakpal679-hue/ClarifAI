"""
Single-owner authorization permissions with IDOR protection (PRD Ch. 26.2, 27, 30.8).
"""
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to access or edit it.
    
    CRITICAL SECURITY POSTURE (PRD Ch. 26.2 & Ch. 30.8):
    When an object exists but is NOT owned by request.user, this permission raises
    rest_framework.exceptions.NotFound (HTTP 404), NEVER HTTP 403 Forbidden.
    This prevents resource existence enumeration / IDOR information disclosure.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Dynamically resolve resource owner field ('user' or 'owner')
        owner = getattr(obj, 'user', None)
        if owner is None:
            owner = getattr(obj, 'owner', None)

        if owner != request.user:
            # Raise 404 Not Found to prevent resource existence disclosure
            raise NotFound("Requested resource was not found.")

        return True
