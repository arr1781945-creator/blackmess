import uuid
import secrets
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.backends import ModelBackend
from .models import BankUser, LoginSession, UserPublicKey
from .serializers import BankUserSerializer as UserSerializer, BankUserCreateSerializer, UserPublicKeySerializer as PublicKeySerializer, UserProfileSerializer
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = ModelBackend().authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'detail': 'Account disabled'}, status=status.HTTP_403_FORBIDDEN)
        refresh = RefreshToken.for_user(user)
        refresh['employee_id'] = str(user.employee_id or '')
        refresh['clearance'] = user.clearance_level
        refresh['mfa_verified'] = False
        try:
            LoginSession.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                refresh_jti=secrets.token_hex(16),
            )
        except Exception as e:
            logger.warning(f"LoginSession create failed: {e}")
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'mfa_required': user.mfa_devices.filter(is_confirmed=True).exists(),
        })


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
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
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class MeProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = request.user
        user_data = {k: v for k, v in request.data.items()
                     if k in ['first_name', 'last_name', 'department', 'avatar_ipfs_cid']}
        if user_data:
            for k, v in user_data.items():
                setattr(user, k, v)
            user.save(update_fields=list(user_data.keys()))

        profile_data = {k: v for k, v in request.data.items()
                        if k in ['title', 'bio_encrypted', 'timezone', 'locale', 'notification_prefs', 'theme']}
        if profile_data:
            from .models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            for k, v in profile_data.items():
                setattr(profile, k, v)
            profile.save(update_fields=list(profile_data.keys()))

        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not user.check_password(old_password):
            return Response({'detail': 'Wrong password'}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed'})


class SessionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = LoginSession.objects.filter(user=request.user).order_by('-created_at')[:10]
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
