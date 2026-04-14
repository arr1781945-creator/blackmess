"""
apps/users/middleware.py

LOW FIX — ForceHTTPSMiddleware: middleware ini override header HTTPS
  secara unconditional, bahkan di production yang sudah HTTPS via proxy.
  Masalah:
  1. Di production dengan reverse proxy (Railway, Nginx), header ini
     sudah di-set oleh proxy — override di sini redundant tapi tidak
     berbahaya jika konsisten.
  2. Lebih tepat gunakan Django setting SECURE_PROXY_SSL_HEADER dan
     SECURE_SSL_REDIRECT daripada middleware custom.
  3. Middleware ini tidak boleh aktif di local development karena
     akan membuat social-auth berpikir semua request adalah HTTPS
     padahal tidak.

  Fix: Middleware sekarang hanya aktif jika USE_FORCE_HTTPS=True di
  settings, atau jika ada header X-Forwarded-Proto dari proxy.
  Untuk production di Railway/Heroku, gunakan settings Django native:

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = not DEBUG

  Middleware ini bisa dihapus setelah settings di atas dikonfigurasi.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class ForceHTTPSMiddleware:
    """
    Paksa request dianggap HTTPS untuk social_django di balik proxy.

    FIX: Hanya aktif jika:
    1. settings.USE_FORCE_HTTPS = True (set di environment production), ATAU
    2. Ada header X-Forwarded-Proto: https dari proxy upstream

    Jika keduanya tidak ada, middleware ini no-op.

    DIREKOMENDASIKAN: Gantikan middleware ini dengan Django native settings:
      SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
      SECURE_SSL_REDIRECT = True  # hanya di production
    Dan hapus middleware ini dari MIDDLEWARE list.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.force_https = getattr(settings, "USE_FORCE_HTTPS", False)

        if self.force_https:
            logger.info(
                "ForceHTTPSMiddleware aktif via USE_FORCE_HTTPS=True. "
                "Pertimbangkan ganti ke SECURE_PROXY_SSL_HEADER di settings."
            )

    def __call__(self, request):
        forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")

        # Aktif hanya jika USE_FORCE_HTTPS=True di settings
        # ATAU jika proxy sudah kirim X-Forwarded-Proto: https
        if self.force_https or forwarded_proto == "https":
            request.META["wsgi.url_scheme"] = "https"
            request.META["HTTP_X_FORWARDED_PROTO"] = "https"

        return self.get_response(request)
