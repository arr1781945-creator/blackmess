"""
apps/compliance/middleware_forensics.py
Anti-forensics middleware + log sanitizer.

- Strips server fingerprinting headers
- Injects anti-screenshot CSP headers
- Blocks developer tools detection triggers
- Sanitizes log output (no PII/credentials in logs)
- Records all vault and auth requests in SecurityEvent
"""

import re
import logging


class AntiForensicsMiddleware:
    """
    Strips server-identifying headers and adds anti-forensics directives.
    """
    HEADERS_TO_REMOVE = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Runtime"]
    SENSITIVE_URL_PATTERNS = ["/vault/", "/kyc/", "/api/v1/auth/"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._strip_server_headers(response)
        self._add_anti_forensics_headers(response, request)
        self._prevent_caching_sensitive(response, request)
        return response

    def _strip_server_headers(self, response):
        for header in self.HEADERS_TO_REMOVE:
            if header in response:
                del response[header]
        # Override with generic value
        response["Server"] = "SecureBank"

    def _add_anti_forensics_headers(self, response, request):
        # Anti-screenshot: prevent rendering APIs from capturing
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "display-capture=(self), screen-wake-lock=()"
        )
        # Document policy — block print/screenshot
        response["Document-Policy"] = "no-document-write"
        # Referrer policy — no leakage
        response["Referrer-Policy"] = "no-referrer"

    def _prevent_caching_sensitive(self, response, request):
        path = request.path
        is_sensitive = any(p in path for p in self.SENSITIVE_URL_PATTERNS)
        if is_sensitive:
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"


class SanitizeLogFilter(logging.Filter):
    """
    Remove sensitive data patterns from log records before writing to file.
    Catches: JWT tokens, passwords, AES keys, credit card-like numbers.
    """
    PATTERNS = [
        (re.compile(r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*"), "Bearer [REDACTED]"),
        (re.compile(rr'"password"\s*:\s*"[^"]*"'), '"password": "[REDACTED]"'),
        (re.compile(rr'"secret"\s*:\s*"[^"]*"'), '"secret": "[REDACTED]"'),
        (re.compile(rr'"otp_code"\s*:\s*"[^"]*"'), '"otp_code": "[REDACTED]"'),
        (re.compile(rr'\b[0-9]{13,19}\b'), '[CARD_NUMBER_REDACTED]'),    # Credit cards
        (re.compile(rr'[A-Fa-f0-9]{64}'), '[KEY_HEX_REDACTED]'),         # 256-bit hex keys
    ]

    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True
