"""
apps/users/pq_mfa.py
Post-Quantum MFA Layer — ML-DSA-65 (Dilithium3 NIST FIPS 204)
Lapisan tambahan di atas WebAuthn/FIDO2 yang sudah ada.

Flow:
  1. POST /auth/pq/register/   → generate Dilithium keypair, simpan public key
  2. POST /auth/pq/challenge/  → server kirim challenge (one-time, TTL 30s)
  3. POST /auth/pq/verify/     → verifikasi Dilithium signature + issue JWT

Ini TIDAK mengganti WebAuthn — ini layer tambahan di atasnya.
JWT yang dihasilkan punya flag pq_verified: true
"""

import os
import json
import base64
import hashlib
import time
import logging
from datetime import datetime, timezone

from django.core.cache import cache
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import BankUser, MFADevice
from .utils_pqc import (
    generate_dilithium_keypair,
    dilithium_sign,
    dilithium_verify,
    OQS_AVAILABLE,
)

logger = logging.getLogger(__name__)

CHALLENGE_TTL = 30  # detik
CACHE_PREFIX = "pq_challenge:"


# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────
def _issue_challenge(user_id: str) -> dict:
    """Buat challenge one-time dengan TTL."""
    raw = os.urandom(32)
    challenge_b64 = base64.b64encode(raw).decode()
    issued_at = time.time()

    cache_key = f"{CACHE_PREFIX}{user_id}"
    cache.set(cache_key, {
        "challenge": challenge_b64,
        "issued_at": issued_at,
        "used": False,
    }, timeout=CHALLENGE_TTL)

    return {
        "challenge": challenge_b64,
        "issued_at": issued_at,
        "expires_in": CHALLENGE_TTL,
        "origin": getattr(settings, "WEBAUTHN_RP_ID", "blackmess.id"),
        "algorithm": "ML-DSA-65",
    }


def _verify_challenge(user_id: str, challenge_b64: str) -> tuple[bool, str]:
    """Cek challenge valid, belum dipakai, belum expired."""
    cache_key = f"{CACHE_PREFIX}{user_id}"
    data = cache.get(cache_key)

    if not data:
        return False, "Challenge tidak ditemukan atau sudah expired"

    if data.get("used"):
        return False, "Challenge sudah digunakan (replay attack dicegah)"

    if data["challenge"] != challenge_b64:
        return False, "Challenge tidak cocok"

    # Tandai sudah dipakai
    data["used"] = True
    cache.set(cache_key, data, timeout=10)

    return True, "OK"


# ─────────────────────────────────────────────────────────────
# VIEW 1: Register Dilithium keypair
# ─────────────────────────────────────────────────────────────
class PQMFARegisterView(APIView):
    """
    POST /auth/pq/register/
    Generate Dilithium keypair untuk user.
    Private key dikembalikan ke client — TIDAK disimpan di server.
    Public key disimpan di MFADevice.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not OQS_AVAILABLE:
            return Response(
                {"detail": "PQC tidak tersedia di server ini."},
                status=503
            )

        user = request.user

        # Cek sudah punya PQ device?
        existing = user.mfa_devices.filter(
            device_type="pq_dilithium",
            is_confirmed=True
        ).first()

        if existing and not request.data.get("force_rotate", False):
            return Response({
                "detail": "PQ MFA sudah terdaftar. Gunakan force_rotate=true untuk rotasi kunci.",
                "registered_at": existing.created_at.isoformat(),
            })

        # Generate keypair
        try:
            pk_b64, sk_b64 = generate_dilithium_keypair()
        except Exception as e:
            logger.error("Dilithium keygen failed: %s", e)
            return Response({"detail": "Gagal generate keypair."}, status=500)

        # Simpan public key di server
        device_name = request.data.get("device_name", "PQ Authenticator")
        MFADevice.objects.update_or_create(
            user=user,
            device_type="pq_dilithium",
            defaults={
                "name": device_name,
                "secret_encrypted": json.dumps({
                    "public_key_b64": pk_b64,
                    "algorithm": "ML-DSA-65",
                    "registered_at": datetime.now(timezone.utc).isoformat(),
                }),
                "is_confirmed": True,
            }
        )

        logger.info("PQ MFA registered for user=%s", user.id)

        return Response({
            "detail": "PQ MFA berhasil didaftarkan.",
            "algorithm": "ML-DSA-65",
            "public_key_fingerprint": hashlib.sha256(
                base64.b64decode(pk_b64)
            ).hexdigest()[:16],
            # Private key dikembalikan ke client — simpan baik-baik!
            "private_key_b64": sk_b64,
            "warning": "Simpan private_key_b64 di tempat aman. Server tidak menyimpan private key.",
        })


# ─────────────────────────────────────────────────────────────
# VIEW 2: Issue challenge
# ─────────────────────────────────────────────────────────────
class PQMFAChallengeView(APIView):
    """
    POST /auth/pq/challenge/
    Server kirim challenge one-time untuk ditandatangani client.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        if not username:
            return Response({"detail": "Username diperlukan."}, status=400)

        try:
            user = BankUser.objects.get(username=username)
        except BankUser.DoesNotExist:
            return Response({"detail": "User tidak ditemukan."}, status=404)

        # Cek punya PQ device
        device = user.mfa_devices.filter(
            device_type="pq_dilithium",
            is_confirmed=True
        ).first()

        if not device:
            return Response(
                {"detail": "PQ MFA belum terdaftar untuk user ini."},
                status=404
            )

        challenge_data = _issue_challenge(str(user.id))
        logger.info("PQ challenge issued for user=%s", user.id)

        return Response(challenge_data)


# ─────────────────────────────────────────────────────────────
# VIEW 3: Verify signature + issue JWT
# ─────────────────────────────────────────────────────────────
class PQMFAVerifyView(APIView):
    """
    POST /auth/pq/verify/
    Body: { username, challenge, signature_b64 }

    Client harus sign: SHA-256(challenge + origin + issued_at)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        challenge_b64 = request.data.get("challenge")
        signature_b64 = request.data.get("signature_b64")

        if not all([username, challenge_b64, signature_b64]):
            return Response(
                {"detail": "username, challenge, dan signature_b64 diperlukan."},
                status=400
            )

        # Ambil user
        try:
            user = BankUser.objects.get(username=username)
        except BankUser.DoesNotExist:
            return Response({"detail": "User tidak ditemukan."}, status=404)

        # Verifikasi challenge
        ok, reason = _verify_challenge(str(user.id), challenge_b64)
        if not ok:
            logger.warning("PQ challenge verify failed user=%s reason=%s", user.id, reason)
            return Response({"detail": reason}, status=401)

        # Ambil public key dari MFADevice
        device = user.mfa_devices.filter(
            device_type="pq_dilithium",
            is_confirmed=True
        ).first()

        if not device:
            return Response({"detail": "PQ MFA device tidak ditemukan."}, status=404)

        try:
            device_data = json.loads(device.secret_encrypted)
            pk_b64 = device_data["public_key_b64"]
        except Exception:
            return Response({"detail": "Data device korup."}, status=500)

        # Buat message yang sama seperti yang client sign
        message = hashlib.sha256(
            challenge_b64.encode() +
            getattr(settings, "WEBAUTHN_RP_ID", "blackmess.id").encode()
        ).digest()

        # Verifikasi signature Dilithium
        try:
            valid = dilithium_verify(pk_b64, message, signature_b64)
        except Exception as e:
            logger.error("Dilithium verify error user=%s: %s", user.id, e)
            return Response({"detail": "Verifikasi signature gagal."}, status=401)

        if not valid:
            logger.warning("Invalid PQ signature user=%s", user.id)
            return Response(
                {"detail": "Signature tidak valid."},
                status=401
            )

        # Update last_used
        device.save(update_fields=["last_used"])

        # Issue JWT dengan flag pq_verified
        refresh = RefreshToken.for_user(user)
        refresh["pq_verified"] = True
        refresh["pq_algorithm"] = "ML-DSA-65"
        refresh["mfa_verified"] = True
        refresh["clearance"] = user.clearance_level

        logger.info("PQ MFA verified + JWT issued for user=%s", user.id)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user.username,
            "pq_verified": True,
            "algorithm": "ML-DSA-65",
        })
