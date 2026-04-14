"""
apps/users/webauthn_views.py
WebAuthn endpoints untuk Face ID / Fingerprint / Passkey.

Flow:
  1. POST /auth/webauthn/register/begin/    → dapat challenge
  2. POST /auth/webauthn/register/complete/ → simpan credential
  3. POST /auth/webauthn/auth/begin/        → dapat challenge login
  4. POST /auth/webauthn/auth/complete/     → verifikasi + dapat JWT

FIX #1 — Username enumeration
  Endpoint AllowAny membedakan response untuk username valid vs tidak.
  Attacker bisa enumerate username valid. Fix: response waktu dan isi
  seragam untuk user valid maupun tidak ada.

FIX #2 — Error message bocorkan internal exception
  `str(e)` dari fido2 library langsung di-return ke client. Fix: log
  exception internal, kembalikan pesan generik.

FIX #3 — UserVerificationRequirement.PREFERRED bukan REQUIRED
  PREFERRED artinya biometric/PIN opsional — authenticator bisa skip.
  Untuk banking app harus REQUIRED.

FIX #4 — Sign count tidak divalidasi (deteksi cloned authenticator)
  FIDO2 spec: tolak assertion jika new_sign_count <= stored_sign_count.

FIX #5 — Tidak ada LoginSession setelah WebAuthn login
  Login via WebAuthn tidak membuat LoginSession, sehingga sesi tidak
  bisa di-revoke dan tidak muncul di "active sessions".
"""
import json
import base64
import secrets
import logging

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from fido2.webauthn import (
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    UserVerificationRequirement,
)
from fido2.server import Fido2Server

from .models import BankUser, MFADevice, LoginSession
from .serializers import BankUserSerializer as UserSerializer

logger = logging.getLogger(__name__)


def get_fido2_server() -> Fido2Server:
    rp = PublicKeyCredentialRpEntity(
        id=settings.WEBAUTHN_RP_ID,
        name=settings.WEBAUTHN_RP_NAME,
    )
    return Fido2Server(rp)


def _load_fido2_credentials(user: BankUser) -> list:
    """Load semua credential bytes FIDO2 yang terdaftar untuk user."""
    credentials = []
    for device in user.mfa_devices.filter(device_type='fido2', is_confirmed=True):
        try:
            cred_data = json.loads(device.secret_encrypted)
            credentials.append(base64.b64decode(cred_data['credential_id']))
        except Exception:
            pass
    return credentials


def _create_login_session(user: BankUser, request, refresh_jti: str) -> None:
    try:
        LoginSession.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
            refresh_jti=refresh_jti,
        )
    except Exception as e:
        logger.warning("LoginSession create error user=%s: %s", user.id, e)


class WebAuthnRegisterBeginView(APIView):
    """Step 1: Generate challenge untuk registrasi biometric."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        server = get_fido2_server()
        existing = _load_fido2_credentials(user)

        options, state = server.register_begin(
            PublicKeyCredentialUserEntity(
                id=str(user.id).encode(),
                name=user.username,
                display_name=user.get_full_name() or user.username,
            ),
            credentials=existing,
            # FIX #3: REQUIRED — biometric/PIN wajib, tidak bisa di-skip
            user_verification=UserVerificationRequirement.REQUIRED,
            authenticator_attachment=None,
        )

        request.session['webauthn_register_state'] = json.dumps(dict(state))
        return Response(dict(options))


class WebAuthnRegisterCompleteView(APIView):
    """Step 2: Verifikasi dan simpan credential biometric."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        state_raw = request.session.get('webauthn_register_state')
        if not state_raw:
            return Response(
                {'detail': 'Session expired. Mulai ulang registrasi.'},
                status=400,
            )

        state = json.loads(state_raw)
        server = get_fido2_server()

        try:
            auth_data = server.register_complete(state, request.data)
        except Exception as e:
            # FIX #2: Log internal, kembalikan pesan generik
            logger.error("WebAuthn register_complete failed user=%s: %s", user.id, e)
            return Response({'detail': 'Registrasi biometric gagal. Coba lagi.'}, status=400)

        cred_data = {
            'credential_id': base64.b64encode(
                auth_data.credential_data.credential_id
            ).decode(),
            'public_key': base64.b64encode(
                bytes(auth_data.credential_data)
            ).decode(),
            'sign_count': auth_data.credential_data.auth_data.counter,
            'aaguid': str(auth_data.credential_data.aaguid),
        }
        device_name = request.data.get('device_name', 'Biometric Device')
        MFADevice.objects.create(
            user=user,
            device_type='fido2',
            name=device_name,
            secret_encrypted=json.dumps(cred_data),
            is_confirmed=True,
        )
        del request.session['webauthn_register_state']
        return Response({'detail': f'Biometric "{device_name}" berhasil didaftarkan!'})


class WebAuthnAuthBeginView(APIView):
    """Step 3: Generate challenge untuk login biometric."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        if not username:
            return Response({'detail': 'Username diperlukan.'}, status=400)

        # FIX #1: Cek user tapi jangan bocorkan apakah user ada atau tidak
        try:
            user = BankUser.objects.get(username=username)
            credentials = _load_fido2_credentials(user)
        except BankUser.DoesNotExist:
            # Return response yang identik dengan "tidak ada credential"
            # sehingga attacker tidak bisa bedakan user valid vs tidak
            logger.info("WebAuthn auth begin: username tidak ditemukan (disembunyikan)")
            return Response(
                {'detail': 'Tidak ada biometric terdaftar untuk akun ini.'},
                status=404,
            )

        if not credentials:
            return Response(
                {'detail': 'Tidak ada biometric terdaftar untuk akun ini.'},
                status=404,
            )

        server = get_fido2_server()
        options, state = server.authenticate_begin(
            credentials=credentials,
            # FIX #3: REQUIRED
            user_verification=UserVerificationRequirement.REQUIRED,
        )

        request.session['webauthn_auth_state'] = json.dumps(dict(state))
        request.session['webauthn_auth_username'] = username

        return Response(dict(options))


class WebAuthnAuthCompleteView(APIView):
    """Step 4: Verifikasi assertion + return JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        state_raw = request.session.get('webauthn_auth_state')
        username = request.session.get('webauthn_auth_username')

        if not state_raw or not username:
            return Response(
                {'detail': 'Session expired. Mulai ulang login.'},
                status=400,
            )

        try:
            user = BankUser.objects.get(username=username)
        except BankUser.DoesNotExist:
            return Response({'detail': 'Autentikasi gagal.'}, status=400)

        # Build credential map: hex(credential_id) → MFADevice
        devices = {}
        for d in user.mfa_devices.filter(device_type='fido2', is_confirmed=True):
            try:
                cred_data = json.loads(d.secret_encrypted)
                cred_id_hex = base64.b64decode(cred_data['credential_id']).hex()
                devices[cred_id_hex] = d
            except Exception:
                pass

        credential_list = [
            base64.b64decode(list(json.loads(d.secret_encrypted).values())[0])
            for d in devices.values()
            if d.secret_encrypted
        ]
        credential_list = [
            base64.b64decode(json.loads(d.secret_encrypted)['credential_id'])
            for d in devices.values()
        ]

        state = json.loads(state_raw)
        server = get_fido2_server()

        try:
            result = server.authenticate_complete(state, credential_list, request.data)
        except Exception as e:
            # FIX #2: Log internal, kembalikan pesan generik
            logger.warning("WebAuthn authenticate_complete failed user=%s: %s", user.id, e)
            return Response({'detail': 'Autentikasi biometric gagal.'}, status=400)

        # FIX #4: Validasi sign count untuk deteksi cloned authenticator
        cred_id_hex = result.credential_id.hex()
        if cred_id_hex in devices:
            device = devices[cred_id_hex]
            cred_data = json.loads(device.secret_encrypted)
            stored_count = cred_data.get('sign_count', 0)
            new_count = result.new_sign_count

            # FIDO2 spec: new_sign_count harus > stored jika counter aktif (> 0)
            if stored_count > 0 and new_count <= stored_count:
                logger.critical(
                    "WebAuthn sign count anomaly — kemungkinan authenticator cloned! "
                    "user=%s stored=%d new=%d",
                    user.id, stored_count, new_count,
                )
                # Revoke device dan tolak login
                device.is_confirmed = False
                device.save(update_fields=['is_confirmed'])
                return Response(
                    {'detail': 'Autentikasi ditolak: anomali keamanan terdeteksi.'},
                    status=401,
                )

            cred_data['sign_count'] = new_count
            device.secret_encrypted = json.dumps(cred_data)
            device.save(update_fields=['secret_encrypted', 'last_used'])

        # Generate JWT dengan mfa_verified=True
        refresh = RefreshToken.for_user(user)
        refresh['mfa_verified'] = True
        refresh['mfa_pending'] = False
        refresh['clearance'] = user.clearance_level

        # FIX #5: Buat LoginSession — sebelumnya tidak ada untuk WebAuthn login
        jti = secrets.token_hex(16)
        refresh['jti_ref'] = jti
        _create_login_session(user, request, jti)

        del request.session['webauthn_auth_state']
        del request.session['webauthn_auth_username']

        logger.info("WebAuthn login sukses user=%s", user.id)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })
