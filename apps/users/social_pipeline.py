import secrets
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def attach_jwt(backend, user, response, *args, **kwargs):
    """Setelah OAuth sukses, generate JWT dan redirect ke frontend."""
    if not user:
        return

    refresh = RefreshToken.for_user(user)
    refresh[r'employee_id'] = str(user.employee_id or '')
    refresh[r'clearance'] = user.clearance_level
    refresh[r'mfa_verified'] = False

    access = str(refresh.access_token)
    refresh_token = str(refresh)

    # Simpan token di session, nanti diambil oleh callback view
    if kwargs.get(r'request'):
        kwargs[r'request'].session['oauth_access'] = access
        kwargs[r'request'].session['oauth_refresh'] = refresh_token
