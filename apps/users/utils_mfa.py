"""
apps/users/utils_mfa.py
MFA utilities: TOTP generation, QR URI, OTP verification, Axes lockout handler.

LOW FIX — verify_totp: valid_window=1 terlalu longgar untuk banking app
  valid_window=1 artinya kode yang sudah expired hingga 30 detik ke belakang
  masih diterima (total window 90 detik: -30s, now, +30s).
  Untuk banking, valid_window=0 lebih tepat — hanya kode window saat ini.
  Clock drift ditangani di level NTP server, bukan di TOTP window.

  Fungsi ini tetap expose valid_window sebagai parameter agar caller
  bisa override jika memang perlu (mis. untuk backward compat sementara),
  tapi default berubah ke 0.
"""
import pyotp
import qrcode
import io
import base64
import logging

logger = logging.getLogger(__name__)

# Default valid_window untuk banking — hanya window saat ini
# Ganti ke 1 jika ada masalah clock drift yang signifikan
_DEFAULT_VALID_WINDOW = 0


def generate_totp_secret() -> str:
    """Generate a new random TOTP base32 secret (32 chars = 160-bit entropy)."""
    return pyotp.random_base32(length=32)


def get_totp_qr_uri(secret: str, username: str, issuer: str = "BlackMess") -> str:
    """Return the otpauth:// URI untuk QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def get_totp_qr_image_b64(secret: str, username: str) -> str:
    """Return base64-encoded PNG QR code image."""
    uri = get_totp_qr_uri(secret, username)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def verify_totp(secret: str, code: str, valid_window: int = _DEFAULT_VALID_WINDOW) -> bool:
    """
    Verify kode TOTP.

    FIX: Default valid_window berubah dari 1 → 0.
    valid_window=1 sebelumnya memberi window 90 detik total (terlalu lebar
    untuk banking). valid_window=0 hanya terima kode window saat ini (30 detik).

    Parameter valid_window tetap ada untuk fleksibilitas, tapi caller harus
    eksplisit jika ingin window lebih lebar.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)


def axes_lockout_handler(request, credentials=None, *args, **kwargs):
    """
    Dipanggil oleh django-axes saat account di-lockout.
    Log security event dan return 429.
    """
    from django.http import JsonResponse
    from apps.compliance.utils import log_security_event

    username = (credentials or {}).get("username", "unknown")
    ip = request.META.get("REMOTE_ADDR", "unknown")

    logger.warning("ACCOUNT_LOCKED: %s from IP %s", username, ip)
    log_security_event("ACCOUNT_LOCKED", request, None, extra=credentials)

    return JsonResponse(
        {"detail": "Akun sementara dikunci karena terlalu banyak percobaan gagal. Coba lagi dalam 1 jam."},
        status=429,
    )
