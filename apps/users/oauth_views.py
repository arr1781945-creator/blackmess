"""
apps/users/oauth_views.py

FIX: Token JWT tidak lagi dikirim via URL query parameter.
     Sebelumnya: redirect ke ?access=TOKEN&refresh=TOKEN
     → token masuk ke server access log, browser history, referrer header.

     Sekarang: redirect ke frontend hanya dengan one-time `state` key.
     Frontend kemudian POST ke /auth/oauth/token/ dengan state key tersebut
     untuk mengambil token — token hanya berpindah via response body HTTPS,
     tidak pernah masuk URL.
"""
import secrets
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# TTL untuk one-time state key — cukup 60 detik untuk frontend ambil token
_STATE_TTL = 60


def oauth_callback(request):
    """
    Dipanggil setelah social-auth selesai. Simpan token ke cache dengan
    one-time state key, lalu redirect frontend ke URL tanpa token.

    Frontend menerima ?state=KEY (bukan token) di URL, lalu langsung
    POST ke /auth/oauth/token/ untuk tukar state → token.
    State key expire dalam 60 detik dan hanya bisa dipakai sekali.
    """
    access = request.session.pop(r'oauth_access', None)
    refresh = request.session.pop(r'oauth_refresh', None)

    frontend = settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL

    if not access:
        return HttpResponseRedirect(f"{frontend}/auth/error?reason=oauth_failed")

    # Buat one-time state key — 32 bytes = 256-bit entropy
    state_key = secrets.token_urlsafe(32)
    cache_key = f"oauth_state:{state_key}"

    cache.set(cache_key, {
        r'access': access,
        r'refresh': refresh,
    }, timeout=_STATE_TTL)

    # Hanya state key yang masuk URL — bukan token
    return HttpResponseRedirect(f"{frontend}/auth/callback?state={state_key}")


@api_view([r'POST'])
@permission_classes([AllowAny])
def oauth_token_exchange(request):
    """
    POST /auth/oauth/token/
    Body: { "state": "<state_key>" }

    Frontend tukar state key → token. Endpoint ini:
    - Hanya bisa dipanggil sekali (state key langsung dihapus)
    - State expire dalam 60 detik
    - Token dikembalikan via response body, tidak pernah lewat URL
    """
    state_key = request.data.get(r'state', '').strip()

    if not state_key:
        return Response({r'detail': 'state diperlukan.'}, status=400)

    cache_key = f"oauth_state:{state_key}"
    token_data = cache.get(cache_key)

    if not token_data:
        # State tidak ditemukan atau sudah expired/dipakai
        return Response({r'detail': 'State tidak valid atau sudah expired.'}, status=400)

    # Hapus segera — one-time use
    cache.delete(cache_key)

    return Response({
        r'access': token_data['access'],
        r'refresh': token_data['refresh'],
    })
