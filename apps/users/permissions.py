"""
apps/users/permissions.py

LOW FIX — IsMFAVerified: tambah cek token claim mfa_verified
  Sebelumnya hanya cek user.is_mfa_verified (field DB persisten).
  Karena fix di serializers.py mfa_verified sekarang selalu False
  saat token pertama di-issue, permission ini harus juga cek claim
  di JWT token agar konsisten dengan flow baru.

  Prioritas cek:
  1. Token claim mfa_verified (dari JWT) — state sesi saat ini
  2. Fallback ke user.is_mfa_verified jika tidak ada token claim
     (backward compat untuk token lama sebelum fix ini)
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
    """
    Izinkan akses hanya jika MFA sudah diverifikasi di sesi ini.

    FIX: Cek JWT token claim mfa_verified terlebih dulu (state sesi saat ini),
    bukan hanya user.is_mfa_verified (state persisten DB).

    Dengan fix di serializers.py, mfa_verified=False saat login,
    lalu di-set True setelah user selesaikan MFA. Permission ini
    memastikan enforcement terjadi per-sesi, bukan per-user lifetime.
    """
    message = "Verifikasi MFA diperlukan untuk mengakses resource ini."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # FIX: Cek JWT claim dulu (state sesi ini)
        # request.auth adalah token object dari simplejwt jika pakai JWTAuthentication
        if request.auth is not None:
            try:
                # simplejwt token mendukung akses seperti dict
                token_mfa = request.auth.get("mfa_verified", None)
                if token_mfa is not None:
                    return bool(token_mfa)
            except (AttributeError, TypeError):
                pass

        # Fallback: cek field DB (untuk token lama sebelum fix diterapkan)
        return bool(getattr(user, "is_mfa_verified", False))


class ClearanceLevelPermission(BasePermission):
    """
    Izinkan akses hanya jika user clearance >= required_clearance di view.

    Penggunaan di view:
      class MyView(APIView):
          permission_classes = [IsAuthenticated, ClearanceLevelPermission]
          required_clearance = 3
    """
    message = "Clearance level tidak mencukupi untuk mengakses resource ini."

    def has_permission(self, request, view):
        required = getattr(view, "required_clearance", 1)
        return (
            request.user.is_authenticated
            and getattr(request.user, "clearance_level", 0) >= required
        )


class IsPQVerified(BasePermission):
    """
    Izinkan akses hanya jika PQ MFA sudah diverifikasi di sesi ini.
    Cek JWT claim pq_verified yang di-set oleh PQMFAVerifyView.
    """
    message = "Post-Quantum MFA verification diperlukan."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.auth is not None:
            try:
                return bool(request.auth.get("pq_verified", False))
            except (AttributeError, TypeError):
                pass

        return False
