"""
WebAuthn endpoints untuk Face ID / Fingerprint / Passkey.
Flow:
  1. POST /auth/webauthn/register/begin/   → dapat challenge
  2. POST /auth/webauthn/register/complete/ → simpan credential
  3. POST /auth/webauthn/auth/begin/        → dapat challenge login
  4. POST /auth/webauthn/auth/complete/     → verifikasi + dapat JWT
"""
import json
import base64
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from fido2.webauthn import (
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    UserVerificationRequirement,
    AttestationConveyancePreference,
)
from fido2.server import Fido2Server
from fido2.cbor import decode as cbor_decode
from .models import BankUser, MFADevice


def get_fido2_server():
    rp = PublicKeyCredentialRpEntity(
        id=settings.WEBAUTHN_RP_ID,
        name=settings.WEBAUTHN_RP_NAME,
    )
    return Fido2Server(rp)


class WebAuthnRegisterBeginView(APIView):
    """Step 1: Generate challenge untuk registrasi biometric."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        server = get_fido2_server()

        # Ambil credentials yang sudah terdaftar
        existing = []
        for device in user.mfa_devices.filter(device_type='fido2', is_confirmed=True):
            try:
                cred_data = json.loads(device.secret_encrypted)
                existing.append(base64.b64decode(cred_data['credential_id']))
            except Exception:
                pass

        options, state = server.register_begin(
            PublicKeyCredentialUserEntity(
                id=str(user.id).encode(),
                name=user.username,
                display_name=user.get_full_name() or user.username,
            ),
            credentials=existing,
            user_verification=UserVerificationRequirement.PREFERRED,
            authenticator_attachment=None,  # None = boleh platform (Face ID) atau roaming (YubiKey)
        )

        # Simpan state di session
        request.session['webauthn_register_state'] = json.dumps(dict(state))

        return Response(dict(options))


class WebAuthnRegisterCompleteView(APIView):
    """Step 2: Verifikasi dan simpan credential biometric."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        state_raw = request.session.get('webauthn_register_state')
        if not state_raw:
            return Response({'detail': 'Session expired. Mulai ulang registrasi.'}, status=400)

        state = json.loads(state_raw)
        server = get_fido2_server()

        try:
            auth_data = server.register_complete(
                state,
                request.data,
            )
            # Simpan credential
            cred_data = {
                'credential_id': base64.b64encode(auth_data.credential_data.credential_id).decode(),
                'public_key': base64.b64encode(bytes(auth_data.credential_data)).decode(),
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
        except Exception as e:
            return Response({'detail': f'Registrasi gagal: {str(e)}'}, status=400)


class WebAuthnAuthBeginView(APIView):
    """Step 3: Generate challenge untuk login biometric."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'detail': 'Username diperlukan.'}, status=400)

        try:
            user = BankUser.objects.get(username=username)
        except BankUser.DoesNotExist:
            return Response({'detail': 'User tidak ditemukan.'}, status=404)

        # Ambil semua credential FIDO2 user
        credentials = []
        for device in user.mfa_devices.filter(device_type='fido2', is_confirmed=True):
            try:
                cred_data = json.loads(device.secret_encrypted)
                credentials.append(base64.b64decode(cred_data['credential_id']))
            except Exception:
                pass

        if not credentials:
            return Response({'detail': 'Tidak ada biometric terdaftar untuk user ini.'}, status=404)

        server = get_fido2_server()
        options, state = server.authenticate_begin(
            credentials=credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
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
            return Response({'detail': 'Session expired. Mulai ulang login.'}, status=400)

        try:
            user = BankUser.objects.get(username=username)
        except BankUser.DoesNotExist:
            return Response({'detail': 'User tidak ditemukan.'}, status=404)

        # Ambil credentials
        credentials = []
        devices = {
            base64.b64decode(json.loads(d.secret_encrypted)['credential_id']).hex(): d
            for d in user.mfa_devices.filter(device_type='fido2', is_confirmed=True)
        }
        credential_list = [base64.b64decode(cid) for cid in devices.keys()]

        state = json.loads(state_raw)
        server = get_fido2_server()

        try:
            result = server.authenticate_complete(
                state,
                credential_list,
                request.data,
            )

            # Update sign count
            cred_id_hex = result.credential_id.hex()
            if cred_id_hex in devices:
                device = devices[cred_id_hex]
                cred_data = json.loads(device.secret_encrypted)
                cred_data['sign_count'] = result.new_sign_count
                device.secret_encrypted = json.dumps(cred_data)
                device.save(update_fields=['secret_encrypted', 'last_used'])

            # Generate JWT
            refresh = RefreshToken.for_user(user)
            refresh['mfa_verified'] = True
            refresh['clearance'] = user.clearance_level

            del request.session['webauthn_auth_state']
            del request.session['webauthn_auth_username']

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user.username,
            })
        except Exception as e:
            return Response({'detail': f'Autentikasi gagal: {str(e)}'}, status=400)
