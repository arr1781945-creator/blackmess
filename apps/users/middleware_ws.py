"""
apps/users/middleware_ws.py
Hardened JWT WebSocket middleware dengan anti-MitM protection.

FIX #1: hmac.new() — sudah benar syntaxnya tapi diganti ke hmac.new()
         yang eksplisit agar tidak ambigu.

FIX #2: _used_nonces sebelumnya in-memory set (module-level variable).
         Di multi-process deployment (Gunicorn N workers), setiap worker
         punya set sendiri — replay attack bisa sukses dengan mengirim
         nonce yang sama ke worker berbeda. Fix: pindah ke Redis via cache.

FIX #3: Token JWT via URL query string masuk ke access log. Prioritaskan
         Authorization header, query param hanya sebagai fallback dengan
         warning log.
"""
import hashlib
import hmac
import time
import logging
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.core.cache import cache   # FIX #2: Redis-backed cache

logger = logging.getLogger(__name__)

NONCE_TTL = 300       # 5 menit
NONCE_WINDOW = 30     # toleransi clock drift 30 detik


def _verify_ws_nonce(nonce: str, timestamp: str, signature: str) -> bool:
    """
    Verify WebSocket connection nonce untuk mencegah replay attacks.
    Client harus sign: HMAC-SHA256(nonce:timestamp, SECRET_KEY)

    FIX #2: Nonce tracking pakai Redis (via Django cache) bukan in-memory set,
    sehingga bekerja benar di multi-process/multi-server deployment.
    """
    try:
        ts = int(timestamp)
        now = int(time.time())

        # Cek timestamp window
        if abs(now - ts) > NONCE_WINDOW:
            logger.warning("WS nonce timestamp expired: %s", ts)
            return False

        # FIX #2: Cek replay via Redis — atomic via cache.add()
        # cache.add() hanya sukses jika key BELUM ada → atomic one-time check
        cache_key = f"ws_nonce:{nonce}"
        if not cache.add(cache_key, 1, timeout=NONCE_TTL):
            # Key sudah ada → nonce sudah dipakai sebelumnya
            logger.warning("WS nonce replay detected: %s", nonce)
            return False

        # FIX #1: Verifikasi HMAC — hmac.new() sudah benar, tapi
        # gunakan hmac.new() secara eksplisit dengan named args
        secret = settings.SECRET_KEY.encode()
        message = f"{nonce}:{timestamp}".encode()
        expected = hmac.new(
            key=secret,
            msg=message,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            logger.warning("WS nonce signature invalid")
            # Hapus dari cache agar nonce bisa dicoba ulang dengan signature benar
            # (jangan biarkan nonce "terbakar" karena signature salah dari client legit)
            cache.delete(cache_key)
            return False

        return True

    except (ValueError, TypeError) as e:
        logger.error("WS nonce verify error: %s", e)
        return False


@database_sync_to_async
def get_user_from_token(token_string):
    from apps.users.models import BankUser
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    try:
        token = AccessToken(token_string)
        user_id = token["user_id"]

        # Cek blacklist
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        jti = token.get("jti")
        if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
            logger.warning("Blacklisted token used for WS: %s", jti)
            return AnonymousUser()

        return BankUser.objects.select_related(r'profile').get(id=user_id, is_active=True)
    except (InvalidToken, TokenError, BankUser.DoesNotExist) as e:
        logger.warning("WS auth failed: %s", e)
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from urllib.parse import parse_qs

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)

        nonce = params.get("nonce", [None])[0]
        timestamp = params.get("ts", [None])[0]
        signature = params.get("sig", [None])[0]

        # Verifikasi nonce jika disertakan
        if nonce and timestamp and signature:
            if not _verify_ws_nonce(nonce, timestamp, signature):
                logger.warning("WS connection rejected — nonce invalid")
                scope["user"] = AnonymousUser()
                return await super().__call__(scope, receive, send)

        # FIX #3: Prioritaskan Authorization header — tidak masuk access log
        token = None
        headers = dict(scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode()
        if auth.startswith("Bearer "):
            token = auth[7:]

        # Fallback ke query param — log warning karena masuk access log
        if not token:
            token = params.get("token", [None])[0]
            if token:
                logger.warning(
                    "WS token via query param (masuk access log) — "
                    "gunakan Authorization header. path=%s",
                    scope.get("path", "unknown"),
                )

        if token:
            scope["user"] = await get_user_from_token(token)
            if scope["user"].is_authenticated:
                logger.info(
                    "WS connected: user=%s path=%s",
                    scope["user"].username,
                    scope.get("path", "unknown"),
                )
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
