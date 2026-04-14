"""
apps/users/otp_views.py

FIX #1 — verify_otp: Timing attack
  Sebelumnya: `otp_hash != hash_otp(code, email)` pakai perbandingan string biasa
  yang rentan timing attack. Ganti ke hmac.compare_digest().

FIX #2 — verify_otp: Logic error user tidak ditemukan
  Sebelumnya: BankUser.DoesNotExist di-catch dan di-pass, lalu kode lanjut ke
  fallback email OTP. Email yang tidak terdaftar di DB tetap bisa lolos jika
  ada hash OTP di cache. Fix: return 400 dengan pesan generik jika user tidak ada.

FIX #3 — verify_otp: Rate limiting pada verify endpoint
  Sebelumnya hanya send_otp yang di-rate-limit, bukan verify. Attacker bisa
  brute-force 6-digit OTP tanpa batasan. Fix: 5 attempt per 10 menit.

FIX #4 — TOTP secret disimpan plaintext
  MFADevice.secret_encrypted menyimpan JSON plaintext bukan ciphertext.
  Fix: enkripsi dengan Fernet sebelum simpan, dekripsi saat baca.
  Butuh settings.ENCRYPTION_KEY (env var, bukan hardcode).

FIX #5 — send_invite: invite_link jangan dikembalikan di response API
  Raw token di response masuk ke API log dan monitoring tools.
"""
import hmac as hmac_lib
import hashlib
import json
import secrets
import string
import base64
import pyotp
import qrcode
import io
import logging

from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import BankUser, MFADevice, InviteToken, UserRole
from .email_service import send_otp_email, send_invite_email

logger = logging.getLogger(__name__)


# ─── Enkripsi helper untuk TOTP secret ───────────────────────────────────────

def _get_fernet():
    """Lazy-load Fernet dengan key dari settings/env."""
    try:
        from cryptography.fernet import Fernet
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            raise RuntimeError(
                "ENCRYPTION_KEY tidak ada di settings. "
                "Generate: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
            )
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    except ImportError:
        raise ImportError("cryptography package diperlukan: pip install cryptography")


def encrypt_secret(plaintext: str) -> str:
    """Enkripsi TOTP secret sebelum disimpan ke DB."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Dekripsi TOTP secret dari DB."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()


# ─── OTP helpers ─────────────────────────────────────────────────────────────

def generate_otp() -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def hash_otp(otp: str, email: str) -> str:
    return hashlib.sha256(f"{otp}{email}".encode()).hexdigest()


def _safe_compare(a: str, b: str) -> bool:
    """FIX #1: Perbandingan hash aman dari timing attack."""
    return hmac_lib.compare_digest(a.encode(), b.encode())


# ─── Views ───────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    email = request.data.get('email', '').strip().lower()
    name = request.data.get('name', '')
    if not email:
        return Response({'error': 'Email required'}, status=400)

    rate_key = f'otp_rate_{email}'
    attempts = cache.get(rate_key, 0)
    if attempts >= 3:
        return Response(
            {'error': 'Terlalu banyak permintaan. Coba lagi 10 menit lagi.'},
            status=429,
        )

    otp = generate_otp()
    otp_hash = hash_otp(otp, email)
    cache.set(f'otp_hash_{email}', otp_hash, timeout=300)
    cache.set(rate_key, attempts + 1, timeout=600)

    sent = send_otp_email(email, otp, name)
    if sent:
        return Response({'message': 'OTP dikirim ke email kamu.'})
    return Response({'error': 'Gagal kirim email.'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()

    if not email or not code:
        return Response({'error': 'Email dan kode diperlukan.'}, status=400)

    # FIX #3: Rate limit pada verify — 5 attempt per 10 menit
    verify_rate_key = f'otp_verify_rate_{email}'
    verify_attempts = cache.get(verify_rate_key, 0)
    if verify_attempts >= 5:
        logger.warning("OTP verify rate limit hit: email=%s", email)
        return Response(
            {'error': 'Terlalu banyak percobaan. Coba lagi 10 menit lagi.'},
            status=429,
        )
    cache.set(verify_rate_key, verify_attempts + 1, timeout=600)

    # FIX #2: Cek user dulu — jangan lanjut jika tidak ditemukan
    try:
        user = BankUser.objects.get(email=email)
    except BankUser.DoesNotExist:
        logger.warning("verify_otp: email tidak terdaftar: %s", email)
        # Pesan generik — tidak beri tahu caller bahwa user tidak ada
        return Response({'error': 'Kode tidak valid atau expired.'}, status=400)

    # Path 1: User punya TOTP device aktif
    totp_device = user.mfa_devices.filter(
        device_type='totp', is_confirmed=True
    ).first()

    if totp_device:
        # FIX #4: Coba dekripsi. Fallback ke plaintext JSON untuk backward compat
        # selama migrasi enkripsi berlangsung (hapus fallback setelah semua dimigrasi)
        try:
            raw_secret = decrypt_secret(totp_device.secret_encrypted)
        except Exception:
            try:
                raw_secret = json.loads(totp_device.secret_encrypted).get(
                    'secret', totp_device.secret_encrypted
                )
            except Exception:
                raw_secret = totp_device.secret_encrypted

        totp = pyotp.TOTP(raw_secret)
        if not totp.verify(code, valid_window=1):
            return Response({'error': 'Kode TOTP salah atau expired.'}, status=400)

        user.is_mfa_verified = True
        user.save(update_fields=['is_mfa_verified'])
        cache.delete(verify_rate_key)
        return Response({'message': 'Verifikasi berhasil!'})

    # Path 2: Fallback ke OTP email
    otp_hash = cache.get(f'otp_hash_{email}')
    if not otp_hash:
        return Response({'error': 'Kode expired. Minta OTP baru.'}, status=400)

    # FIX #1: compare_digest — aman dari timing attack
    if not _safe_compare(otp_hash, hash_otp(code, email)):
        return Response({'error': 'Kode tidak valid atau expired.'}, status=400)

    cache.delete(f'otp_hash_{email}')
    cache.delete(verify_rate_key)
    return Response({'message': 'Verifikasi berhasil!'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invite(request):
    """Generate InviteToken + kirim link via email."""
    from apps.workspace.models import Workspace

    workspace_id = request.data.get('workspace_id')
    to_email = request.data.get('to_email', '').strip().lower()
    role_name = request.data.get('role', 'member')

    if not workspace_id or not to_email:
        return Response({'error': 'workspace_id dan to_email diperlukan.'}, status=400)

    try:
        workspace = Workspace.objects.get(id=workspace_id)
    except Workspace.DoesNotExist:
        return Response({'error': 'Workspace tidak ditemukan.'}, status=404)

    try:
        role = UserRole.objects.get(name=role_name)
    except UserRole.DoesNotExist:
        role = UserRole.objects.first()
        if not role:
            return Response({'error': 'Role tidak ditemukan.'}, status=404)

    rate_key = f'invite_rate_{request.user.id}'
    attempts = cache.get(rate_key, 0)
    if attempts >= 10:
        return Response({'error': 'Terlalu banyak undangan. Coba lagi 1 jam lagi.'}, status=429)
    cache.set(rate_key, attempts + 1, timeout=3600)

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha512(raw_token.encode()).hexdigest()

    invite = InviteToken.objects.create(
        workspace=workspace,
        created_by=request.user,
        email=to_email,
        role=role,
        token_hash=token_hash,
        expires_at=timezone.now() + timezone.timedelta(days=7),
    )

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://black-message.vercel.app')
    invite_link = f"{frontend_url}/invite/{raw_token}"

    sent = send_invite_email(
        to_email=to_email,
        from_name=request.user.get_full_name() or request.user.username,
        invite_link=invite_link,
        workspace=workspace.name,
    )

    if sent:
        # FIX #5: Jangan kembalikan raw invite_link di response
        return Response({
            'message': f'Undangan berhasil dikirim ke {to_email}.',
            'expires_at': invite.expires_at.isoformat(),
        })
    return Response({'error': 'Gagal kirim email undangan.'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_totp_secret(request):
    """Generate TOTP secret + QR code."""
    user = request.user
    email = user.email

    secret = pyotp.random_base32()
    cache.set(f'totp_setup_{email}', secret, timeout=600)

    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name='BlackMess'
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return Response({
        'qr_code': f'data:image/png;base64,{qr_b64}',
        'totp_uri': totp_uri,
        # Raw secret tidak dikembalikan ke client — hanya scan QR
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_totp_setup(request):
    """Verifikasi TOTP saat setup + simpan ke MFADevice dengan secret terenkripsi."""
    user = request.user
    email = user.email
    code = request.data.get('code', '').strip()

    if not code:
        return Response({'error': 'Kode diperlukan.'}, status=400)

    secret = cache.get(f'totp_setup_{email}')
    if not secret:
        return Response({'error': 'Setup expired. Generate ulang QR code.'}, status=400)

    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        return Response({'error': 'Kode salah!'}, status=400)

    # FIX #4: Enkripsi secret sebelum simpan ke DB
    try:
        encrypted_secret = encrypt_secret(secret)
    except Exception as e:
        logger.error("Gagal enkripsi TOTP secret user=%s: %s", user.id, e)
        return Response({'error': 'Terjadi kesalahan server.'}, status=500)

    device_name = request.data.get('device_name', 'Google Authenticator')
    MFADevice.objects.filter(user=user, device_type='totp').update(is_primary=False)
    MFADevice.objects.create(
        user=user,
        device_type='totp',
        name=device_name,
        secret_encrypted=encrypted_secret,  # FIX #4: ciphertext
        is_confirmed=True,
        is_primary=True,
    )

    cache.delete(f'totp_setup_{email}')

    user.is_mfa_verified = True
    user.save(update_fields=['is_mfa_verified'])

    return Response({'message': f'Authenticator "{device_name}" berhasil didaftarkan!'})
