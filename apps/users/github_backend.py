"""
apps/users/github_backend.py

LOW FIX — GithubOAuth2HTTPS: dua masalah:

1. REDIRECT_STATE = False menonaktifkan verifikasi OAuth state parameter
   yang merupakan proteksi CSRF pada OAuth flow. Penyebab aslinya adalah
   aplikasi di-detect sebagai HTTP padahal HTTPS.

   Fix root cause: pastikan SECURE_PROXY_SSL_HEADER di-set di settings
   sehingga Django tahu app di balik HTTPS proxy. Dengan itu, social-auth
   akan generate redirect_uri dengan https:// secara natural tanpa
   perlu REDIRECT_STATE=False atau regex patch.

2. auth_url() menggunakan regex untuk ganti http → https di URL
   yang rapuh — jika library mengubah encoding, regex tidak akan match.

   Fix: kedua workaround (REDIRECT_STATE=False dan regex patch) dihapus.
   Gantikan dengan konfigurasi yang benar di settings.py.

CARA PAKAI:
  Di core/settings.py atau settings_oauth_fix.py:

    # Beritahu Django bahwa app di balik HTTPS proxy (Railway/Heroku/Nginx)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Social auth akan pakai https:// secara otomatis
    SOCIAL_AUTH_GITHUB_KEY = env('GITHUB_CLIENT_ID')
    SOCIAL_AUTH_GITHUB_SECRET = env('GITHUB_CLIENT_SECRET')

    # Tidak perlu lagi SOCIAL_AUTH_GITHUB_REDIRECT_URL manual
    # karena Django akan generate yang benar berdasarkan request scheme

  Di AUTHENTICATION_BACKENDS:
    'apps.users.github_backend.GithubOAuth2HTTPS'  # tetap pakai class ini
    # atau ganti ke 'social_core.backends.github.GithubOAuth2' langsung
    # jika tidak perlu override apapun
"""
import os
import logging
from social_core.backends.github import GithubOAuth2

logger = logging.getLogger(__name__)


class GithubOAuth2HTTPS(GithubOAuth2):
    """
    Custom GitHub OAuth2 backend.

    FIX: REDIRECT_STATE dikembalikan ke True (default social-auth).
    Regex patch di auth_url() dihapus.

    Jika masih ada masalah redirect_uri pakai HTTP bukan HTTPS,
    penyebabnya adalah SECURE_PROXY_SSL_HEADER belum di-set di settings.
    Fix di settings, bukan di sini.
    """

    # FIX: REDIRECT_STATE=True (default) — proteksi CSRF OAuth aktif kembali
    # Jika sebelumnya False karena session tidak persistent di multi-server,
    # fix di session backend (pakai Redis), bukan di sini.
    REDIRECT_STATE = True

    def get_redirect_uri(self, state=None):
        """
        Override hanya untuk support SOCIAL_AUTH_GITHUB_CALLBACK_URL
        via env var sebagai fallback eksplisit.
        """
        env_url = os.environ.get("SOCIAL_AUTH_GITHUB_CALLBACK_URL")
        if env_url:
            return env_url

        # Default: biarkan social-auth generate dari request
        # (akan pakai https:// jika SECURE_PROXY_SSL_HEADER di-set benar)
        return super().get_redirect_uri(state=state)
