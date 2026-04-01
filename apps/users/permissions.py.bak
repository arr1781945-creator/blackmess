"""
apps/users/permissions.py — RBAC permission classes
"""
from rest_framework.permissions import BasePermission


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class CanManageUsers(BasePermission):
    def has_permission(self, request, view):
        return request.user.role_assignments.filter(
            role__name__in=["super_admin", "compliance_officer"],
            is_active=True,
        ).exists()


class IsMFAVerified(BasePermission):
    """Block access if MFA is enforced but not yet verified this session."""
    message = "MFA verification required."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_mfa_enforced and not user.is_mfa_verified:
            return False
        return True


class ClearanceLevelPermission(BasePermission):
    """Require a minimum clearance level. Set required_clearance on the view."""
    def has_permission(self, request, view):
        required = getattr(view, "required_clearance", 1)
        return (
            request.user.is_authenticated
            and request.user.clearance_level >= required
        )
