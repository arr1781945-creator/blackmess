"""
apps/users/settings_views.py
Semua endpoint untuk halaman Settings:
  - Profil & avatar
  - Notifikasi
  - Tema
  - Keamanan (password, sesi, 2FA)
  - Privacy
  - API Keys
"""
import json
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import BankUser, UserProfile, LoginSession, MFADevice, APIKey
import secrets
import hashlib


# ─── GET/UPDATE semua settings sekaligus ─────────────────────────────────────

class SettingsView(APIView):
    """GET semua settings user, PATCH update."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response({
            r'profile': {
                r'username': user.username,
                r'email': user.email,
                r'first_name': user.first_name,
                r'last_name': user.last_name,
                r'department': user.department,
                r'employee_id': user.employee_id,
                r'clearance_level': user.clearance_level,
                r'avatar_ipfs_cid': user.avatar_ipfs_cid,
                r'title': profile.title,
                r'timezone': profile.timezone,
                r'locale': profile.locale,
            },
            r'appearance': {
                r'theme': profile.theme,
            },
            r'notifications': profile.notification_prefs or {
                r'email_mentions': True,
                r'email_invites': True,
                r'email_security': True,
                r'push_messages': True,
                r'push_mentions': True,
                r'push_calls': True,
                r'digest_daily': False,
                r'digest_weekly': True,
            },
            r'security': {
                r'is_mfa_enforced': user.is_mfa_enforced,
                r'is_mfa_verified': user.is_mfa_verified,
                r'mfa_devices': [
                    {
                        r'id': str(d.id),
                        r'name': d.name,
                        r'type': d.device_type,
                        r'is_primary': d.is_primary,
                        r'last_used': d.last_used.isoformat() if d.last_used else None,
                    }
                    for d in user.mfa_devices.filter(is_confirmed=True)
                ],
                r'active_sessions_count': LoginSession.objects.filter(
                    user=user, is_revoked=False
                ).count(),
            },
        })

    def patch(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        data = request.data

        # Update BankUser fields
        user_fields = {}
        for field in [r'first_name', 'last_name', 'department', 'avatar_ipfs_cid']:
            if field in data:
                user_fields[field] = data[field]
        if user_fields:
            for k, v in user_fields.items():
                setattr(user, k, v)
            user.save(update_fields=list(user_fields.keys()))

        # Update profile fields
        profile_fields = {}
        for field in [r'title', 'timezone', 'locale', 'theme', 'notification_prefs']:
            if field in data:
                profile_fields[field] = data[field]
        if profile_fields:
            for k, v in profile_fields.items():
                setattr(profile, k, v)
            profile.save(update_fields=list(profile_fields.keys()))

        return Response({r'detail': 'Settings berhasil disimpan!'})


# ─── Notifikasi ───────────────────────────────────────────────────────────────

class NotificationSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(profile.notification_prefs or {})

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        prefs = profile.notification_prefs or {}
        prefs.update(request.data)
        profile.notification_prefs = prefs
        profile.save(update_fields=[r'notification_prefs'])
        return Response({r'detail': 'Preferensi notifikasi disimpan!'})


# ─── Tema / Appearance ────────────────────────────────────────────────────────

class AppearanceSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        theme = request.data.get(r'theme')
        if theme not in [r'dark', 'light']:
            return Response({r'detail': 'Tema harus "dark" atau "light".'}, status=400)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.theme = theme
        profile.save(update_fields=[r'theme'])
        return Response({r'detail': f'Tema diubah ke {theme}!'})


# ─── Keamanan ─────────────────────────────────────────────────────────────────

class SecuritySettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sessions = LoginSession.objects.filter(user=user, is_revoked=False).order_by(r'-created_at')
        devices = user.mfa_devices.filter(is_confirmed=True)

        return Response({
            r'mfa_devices': [
                {
                    r'id': str(d.id),
                    r'name': d.name,
                    r'type': d.device_type,
                    r'is_primary': d.is_primary,
                    r'last_used': d.last_used.isoformat() if d.last_used else None,
                    r'created_at': d.created_at.isoformat(),
                }
                for d in devices
            ],
            r'active_sessions': [
                {
                    r'id': str(s.id),
                    r'ip': s.ip_address,
                    r'device': s.user_agent[:80] if s.user_agent else 'Unknown',
                    r'created_at': s.created_at.isoformat(),
                    r'last_seen': s.last_seen.isoformat() if hasattr(s, 'last_seen') and s.last_seen else None,
                }
                for s in sessions[:10]
            ],
        })


class RevokeSessionView(APIView):
    """Revoke sesi tertentu atau semua sesi."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get(r'session_id')
        revoke_all = request.data.get(r'revoke_all', False)

        if revoke_all:
            count = LoginSession.objects.filter(
                user=request.user, is_revoked=False
            ).update(is_revoked=True)
            return Response({r'detail': f'{count} sesi berhasil dinonaktifkan.'})

        if session_id:
            try:
                session = LoginSession.objects.get(id=session_id, user=request.user)
                session.is_revoked = True
                session.save(update_fields=[r'is_revoked'])
                return Response({r'detail': 'Sesi berhasil dinonaktifkan.'})
            except LoginSession.DoesNotExist:
                return Response({r'detail': 'Sesi tidak ditemukan.'}, status=404)

        return Response({r'detail': 'session_id atau revoke_all diperlukan.'}, status=400)


class RemoveMFADeviceView(APIView):
    """Hapus MFA device."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, device_id):
        try:
            device = MFADevice.objects.get(id=device_id, user=request.user)
            device.delete()
            return Response({r'detail': f'Perangkat "{device.name}" dihapus.'})
        except MFADevice.DoesNotExist:
            return Response({r'detail': 'Perangkat tidak ditemukan.'}, status=404)


# ─── API Keys ─────────────────────────────────────────────────────────────────

class APIKeySettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        keys = APIKey.objects.filter(user=request.user, is_active=True)
        return Response([
            {
                r'id': str(k.id),
                r'name': k.name,
                r'prefix': k.key_prefix,
                r'scopes': k.scopes,
                r'created_at': k.created_at.isoformat(),
                r'expires_at': k.expires_at.isoformat() if k.expires_at else None,
                r'last_used': k.last_used.isoformat() if k.last_used else None,
            }
            for k in keys
        ])

    def post(self, request):
        name = request.data.get(r'name', '').strip()
        scopes = request.data.get(r'scopes', [])

        if not name:
            return Response({r'detail': 'Nama API key diperlukan.'}, status=400)

        # Generate key
        raw_key = f"bm_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha512(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        api_key = APIKey.objects.create(
            user=request.user,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
        )

        return Response({
            r'id': str(api_key.id),
            r'name': api_key.name,
            r'key': raw_key,  # Ditampilkan sekali saja!
            r'prefix': key_prefix,
            r'scopes': scopes,
            r'detail': 'Simpan API key ini sekarang! Tidak akan ditampilkan lagi.',
        }, status=201)

    def delete(self, request):
        key_id = request.data.get(r'id')
        try:
            key = APIKey.objects.get(id=key_id, user=request.user)
            key.is_active = False
            key.save(update_fields=[r'is_active'])
            return Response({r'detail': 'API key dinonaktifkan.'})
        except APIKey.DoesNotExist:
            return Response({r'detail': 'API key tidak ditemukan.'}, status=404)


# ─── Privacy ──────────────────────────────────────────────────────────────────

class PrivacySettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.compliance.models import UserConsent
        consents = UserConsent.objects.filter(user=request.user)
        return Response({
            r'consents': [
                {
                    r'type': c.consent_type,
                    r'version': c.version,
                    r'consented': c.consented,
                    r'consented_at': c.consented_at.isoformat() if c.consented_at else None,
                }
                for c in consents
            ]
        })

    def patch(self, request):
        from apps.compliance.models import UserConsent
        consent_type = request.data.get(r'consent_type')
        consented = request.data.get(r'consented', False)
        version = request.data.get(r'version', 'v1.0')

        if not consent_type:
            return Response({r'detail': 'consent_type diperlukan.'}, status=400)

        consent, _ = UserConsent.objects.get_or_create(
            user=request.user,
            consent_type=consent_type,
            version=version,
        )
        consent.consented = consented
        consent.consented_at = timezone.now() if consented else None
        consent.ip_address = request.META.get(r'REMOTE_ADDR')
        consent.save(update_fields=[r'consented', 'consented_at', 'ip_address'])

        return Response({r'detail': 'Preferensi privasi disimpan!'})
