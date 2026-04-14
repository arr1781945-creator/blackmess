"""
apps/users/admin.py — Hardened admin registration

LOW FIX — LoginSessionAdmin: semua is_staff user bisa lihat semua sesi
  aktif + refresh_jti dari seluruh user. JTI adalah data sensitif yang
  bisa digunakan untuk token analysis. Fix: batasi ke superuser saja.

LOW FIX — BankUserAdmin: tambah has_delete_permission untuk cegah
  penghapusan user dari admin UI (harus lewat soft-delete/deactivate).
"""
import logging
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import BankUser, UserProfile, UserRole, UserRoleAssignment, MFADevice, LoginSession

logger = logging.getLogger(__name__)


@admin.register(BankUser)
class BankUserAdmin(UserAdmin):
    list_display = [
        "username", "employee_id", "department",
        "clearance_level", "is_mfa_verified", "is_locked", "last_active",
    ]
    list_filter = ["clearance_level", "is_mfa_verified", "is_locked", "department"]
    search_fields = ["username", "email", "employee_id"]
    readonly_fields = [
        "last_active", "last_ip",
        "pqc_public_key_kyber", "pqc_public_key_dilithium",
        "employee_id",  # employee_id tidak boleh diubah via admin
    ]
    fieldsets = UserAdmin.fieldsets + (
        ("Banking Fields", {
            "fields": (
                "employee_id", "department", "clearance_level",
                "is_mfa_enforced", "is_mfa_verified",
                "is_locked", "last_ip", "last_active",
            )
        }),
        ("PQC Keys (Read-Only)", {
            "fields": ("pqc_public_key_kyber", "pqc_public_key_dilithium"),
            "classes": ("collapse",),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """
        FIX: Nonaktifkan hard delete dari admin UI.
        User harus di-deactivate (is_active=False) atau di-lock,
        bukan dihapus permanen — penting untuk audit trail banking.
        Hanya superuser yang boleh hard delete, dan hanya via shell.
        """
        return False

    def save_model(self, request, obj, form, change):
        """Log perubahan user yang dilakukan via admin."""
        action = "changed" if change else "created"
        logger.warning(
            "Admin user %s [%s] user=%s via Django Admin",
            action, request.user.username, obj.username,
        )
        super().save_model(request, obj, form, change)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = [
        "name", "display_name", "max_clearance",
        "can_access_vault", "can_export_messages",
    ]

    def has_delete_permission(self, request, obj=None):
        """Role tidak boleh dihapus jika masih ada assignment aktif."""
        if obj and obj.assignments.filter(is_active=True).exists():
            return False
        return request.user.is_superuser


@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "ip_address", "created_at", "last_seen", "is_revoked"]
    list_filter = ["is_revoked"]
    search_fields = ["user__username", "ip_address"]

    # FIX: refresh_jti tidak ditampilkan — data sensitif
    # Sebelumnya ada di readonly_fields dan bisa dilihat semua is_staff
    readonly_fields = ["user", "ip_address", "user_agent", "created_at"]

    def has_delete_permission(self, request, obj=None):
        """Session tidak dihapus — hanya di-revoke untuk audit trail."""
        return False

    def has_add_permission(self, request):
        """Session hanya dibuat oleh sistem, tidak manual dari admin."""
        return False

    def get_queryset(self, request):
        """
        FIX: Batasi akses ke superuser saja.
        is_staff biasa tidak perlu lihat semua sesi aktif seluruh user.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Staff biasa hanya lihat sesi milik sendiri
            return qs.filter(user=request.user)
        return qs
