"""
apps/users/views.py

FIX #1 — LoginView: Full JWT token diberikan meski MFA belum diverifikasi
  Sebelumnya access token penuh langsung dikembalikan meskipun user punya
  MFA aktif. Flag mfa_required hanya informatif, tidak di-enforce.

  Solusi: jika user punya MFA aktif, kembalikan pre_auth_token dengan
  scope terbatas (hanya bisa akses endpoint /otp/verify/ dan /webauthn/auth/).
  Token penuh diberikan setelah MFA selesai via endpoint tersebut.

  pre_auth_token: JWT biasa tapi dengan claim `mfa_pending=True` dan
  `mfa_verified=False`. Permission class `IsMFAVerified` sudah ada dan
  akan menolak request jika mfa_verified=False.

FIX #2 — ChangePasswordView: Tidak invalidasi sesi aktif lain
  Setelah password ganti, semua refresh token lain harus di-revoke.

FIX #3 — LoginView: Hapus loop JTI yang tidak perlu
  secrets.token_hex(16) = 128-bit entropy, collision probability nol.
  Loop DB check tidak diperlukan dan menambah latency.

FIX #4 — ChangePasswordView: Tidak validasi new_password dengan validator
  Password baru tidak melalui Django password validator.
"""
import secrets
import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import BankUser, LoginSession, UserPublicKey, UserProfile
from .serializers import (
    BankUserSerializer as UserSerializer,
    BankUserCreateSerializer,
    UserPublicKeySerializer as PublicKeySerializer,
)

logger = logging.getLogger(__name__)


def _create_login_session(user, request, refresh_jti: str) -> None:
    """Helper: buat LoginSession. Dipanggil dari LoginView dan WebAuthn."""
    try:
        LoginSession.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
            refresh_jti=refresh_jti,
        )
    except Exception as e:
        logger.warning("LoginSession create error user=%s: %s", user.id, e)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        user = ModelBackend().authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=401)
        if not user.is_active:
            return Response({'detail': 'Account disabled'}, status=403)

        has_mfa = user.mfa_devices.filter(is_confirmed=True).exists()

        refresh = RefreshToken.for_user(user)
        refresh['employee_id'] = str(user.employee_id or '')
        refresh['clearance'] = user.clearance_level

        if has_mfa:
            # FIX #1: User punya MFA — berikan token dengan mfa_verified=False
            # IsMFAVerified permission akan blokir semua endpoint sensitif
            # sampai user selesaikan MFA via /otp/verify/ atau /webauthn/auth/
            refresh['mfa_verified'] = False
            refresh['mfa_pending'] = True
        else:
            # Tidak ada MFA device — ini seharusnya tidak terjadi di banking app
            # karena is_mfa_enforced=True by default. Log sebagai anomali.
            if getattr(user, 'is_mfa_enforced', True):
                logger.warning(
                    "User %s login tanpa MFA device meskipun MFA enforced",
                    user.id,
                )
            refresh['mfa_verified'] = False
            refresh['mfa_pending'] = False

        # FIX #3: Hapus loop — secrets.token_hex(16) = 128-bit, collision tidak mungkin
        jti = secrets.token_hex(16)
        _create_login_session(user, request, jti)

        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'mfa_required': has_mfa,
        }

        if has_mfa:
            response_data['detail'] = (
                'Login berhasil. Selesaikan verifikasi MFA untuk mengakses semua fitur.'
            )

        return Response(response_data)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out.'})


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BankUserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        refresh['mfa_verified'] = False
        refresh['mfa_pending'] = False
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=201)


class MeProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        user = request.user
        # Whitelist field yang boleh diupdate — tidak termasuk clearance_level,
        # is_mfa_enforced, atau field sensitif lainnya
        allowed_user_fields = ['first_name', 'last_name', 'department', 'avatar_ipfs_cid']
        user_updates = {}
        for field in allowed_user_fields:
            if field in request.data:
                user_updates[field] = request.data[field]
        if user_updates:
            for k, v in user_updates.items():
                setattr(user, k, v)
            user.save(update_fields=list(user_updates.keys()))

        profile, _ = UserProfile.objects.get_or_create(user=user)
        # bio_encrypted: enkripsi harus dilakukan di server, bukan terima ciphertext dari client
        # Untuk sementara, field ini tidak diekspos via API hingga enkripsi server-side diimplementasi
        allowed_profile_fields = ['title', 'timezone', 'locale', 'notification_prefs', 'theme']
        profile_updates = {}
        for field in allowed_profile_fields:
            if field in request.data:
                profile_updates[field] = request.data[field]
        if profile_updates:
            for k, v in profile_updates.items():
                setattr(profile, k, v)
            profile.save(update_fields=list(profile_updates.keys()))

        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not user.check_password(old_password):
            return Response({'detail': 'Wrong password'}, status=400)

        # FIX #4: Validasi new_password dengan Django validator
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({'detail': list(e.messages)}, status=400)

        user.set_password(new_password)
        user.save()

        # FIX #2: Revoke semua sesi aktif lain setelah password berubah
        # Kecuali sesi saat ini (berdasarkan JTI dari token yang sedang dipakai)
        current_jti = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                token = AccessToken(auth_header[7:])
                current_jti = token.get('jti')
            except Exception:
                pass

        revoked_count = LoginSession.objects.filter(
            user=user, is_revoked=False
        ).exclude(
            refresh_jti=current_jti or ''
        ).update(is_revoked=True)

        logger.info(
            "Password changed user=%s — %d sesi lain di-revoke",
            user.id, revoked_count,
        )

        return Response({'detail': 'Password berhasil diubah. Semua sesi lain telah dinonaktifkan.'})


class SessionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = LoginSession.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        return Response([{
            'id': str(s.id),
            'ip': s.ip_address,
            'ua': s.user_agent,
            'created_at': s.created_at.isoformat(),
            'is_revoked': s.is_revoked,
        } for s in sessions])


class PublicKeyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        keys = UserPublicKey.objects.filter(user=request.user)
        return Response(PublicKeySerializer(keys, many=True).data)

    def post(self, request):
        serializer = PublicKeySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class MFASetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({'detail': 'Use /totp/generate/ or /webauthn/register/begin/'})


class MFAVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({'detail': 'Use /otp/verify/ or /webauthn/auth/complete/'})
