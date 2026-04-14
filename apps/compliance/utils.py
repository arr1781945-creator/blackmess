"""
apps/compliance/utils.py

FIX — secure_exception_handler: hanya scrub 500, bukan 4xx
  Error 400/401/403/404 bisa bocorkan internal detail (field names,
  model structure, query details) di production.
  Fix: scrub semua response >= 400 dari detail internal,
  kecuali field validation errors (400) yang memang perlu dilihat user.
"""
import logging

logger = logging.getLogger("apps.compliance")


def log_security_event(event_type: str, request, user, extra: dict = None):
    """Async-safe security event logger."""
    from .models import SecurityEvent
    try:
        SecurityEvent.objects.create(
            event_type=event_type,
            user=user,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            detail=extra or {},
            is_suspicious=event_type in (
                "LOGIN_FAIL", "ACCOUNT_LOCKED", "MFA_FAIL", "VAULT_ACCESS_DENIED",
                "INVALID_SIGNATURE", "INVALID_INVITE",
            ),
        )
    except Exception as e:
        logger.error("Failed to log security event %s: %s", event_type, e)


def log_event(
    event_type: str,
    description: str,
    severity: str = "info",
    metadata: dict = None,
):
    """Log a system audit event (no request context)."""
    from .models import AuditLog
    try:
        AuditLog.objects.create(
            event_type=event_type,
            severity=severity,
            description=description,
            metadata=metadata or {},
        )
    except Exception as e:
        logger.error("AuditLog write failed: %s", e)


def secure_exception_handler(exc, context):
    """
    DRF exception handler — strip internal details di production.

    FIX: Sebelumnya hanya scrub 500+. Error 4xx juga bisa bocorkan
    informasi internal. Sekarang:
    - 400 (ValidationError): tetap kembalikan field errors — user butuh ini
    - 401, 403: kembalikan pesan generik saja
    - 404: kembalikan pesan generik saja
    - 500+: selalu kembalikan pesan generik
    """
    from rest_framework.views import exception_handler
    from rest_framework.exceptions import ValidationError
    from django.conf import settings

    response = exception_handler(exc, context)

    if response is None:
        return None

    if settings.DEBUG:
        # Di debug mode, tampilkan semua detail untuk development
        return response

    # Production: scrub berdasarkan status code
    if response.status_code >= 500:
        logger.error(
            "Unhandled server error: %s — %s",
            exc.__class__.__name__, exc,
            exc_info=True,
        )
        response.data = {"detail": "Terjadi kesalahan server. Hubungi support."}

    elif response.status_code in (401, 403):
        # Jangan bocorkan alasan spesifik kenapa ditolak
        # (apakah karena tidak login, token expired, clearance kurang, dll)
        if response.status_code == 401:
            response.data = {"detail": "Autentikasi diperlukan."}
        else:
            response.data = {"detail": "Akses ditolak."}

    elif response.status_code == 404:
        # Jangan bocorkan apakah resource tidak ada atau tidak punya akses
        response.data = {"detail": "Resource tidak ditemukan."}

    elif response.status_code == 400 and not isinstance(exc, ValidationError):
        # 400 yang bukan ValidationError (field errors) — scrub detail internal
        response.data = {"detail": "Request tidak valid."}
    # ValidationError 400 tetap dikembalikan apa adanya — user butuh field errors

    return response
