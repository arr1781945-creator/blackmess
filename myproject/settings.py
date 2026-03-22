"""
core/settings.py
SecureBank Slack-Clone — Hardened Django Settings
Implements: HSTS, CSP, PBAC, PQC key loading, Channel Layers, Axes, OTP
"""

import os
from pathlib import Path
from datetime import timedelta
import environ

# ─────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# ─────────────────────────────────────────────
# INSTALLED APPS
# ─────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "channels",
    "corsheaders",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "social_django",
    "django_celery_beat",
    "simple_history",
    "auditlog",
    "drf_spectacular",
    "csp",
]

LOCAL_APPS = [
    "apps.users",
    "apps.workspace",
    "apps.messaging",
    "apps.vault",
    "apps.compliance",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─────────────────────────────────────────────
# MIDDLEWARE — Order is security-critical
# ─────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",          # Must be first
    "corsheaders.middleware.CorsMiddleware",
    "csp.middleware.CSPMiddleware",
    "apps.compliance.middleware_forensics.AntiForensicsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "axes.middleware.AxesMiddleware",                         # Brute-force protection
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "myproject.urls"
ASGI_APPLICATION = "myproject.asgi.application"
WSGI_APPLICATION = "myproject.wsgi.application"

AUTH_USER_MODEL = "users.BankUser"

# ─────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

# ─────────────────────────────────────────────
# DATABASE — PostgreSQL with connection pooling
# ─────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c default_transaction_isolation=serializable",
        },
    }
}

# ─────────────────────────────────────────────
# REDIS — Channel layer + Celery
# ─────────────────────────────────────────────
REDIS_URL = env("REDIS_URL")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
            "capacity": 1500,
            "expiry": 60,
            "symmetric_encryption_keys": [env("AES_MASTER_KEY")[:32]],  # Encrypt channel data
        },
    },
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ─────────────────────────────────────────────
# REST FRAMEWORK
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "200/minute",
        "auth": "5/minute",               # Extra tight for login
        "vault": "10/minute",             # Vault access throttle
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.compliance.utils.secure_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 50,
}

# ─────────────────────────────────────────────
# JWT CONFIG
# ─────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=1))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS512",                 # SHA-512 HMAC
    "SIGNING_KEY": env("JWT_SIGNING_KEY"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.users.serializers.BankTokenObtainPairSerializer",
    "JTI_CLAIM": "jti",
}

# ─────────────────────────────────────────────
# DJANGO AXES — Brute-force lockout
# ─────────────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_CALLABLE = "apps.users.utils_mfa.axes_lockout_handler"
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = True
AXES_VERBOSE = True

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.azuread.AzureADOAuth2",
]

# ─────────────────────────────────────────────
# SECURITY HEADERS — Hardened
# ─────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", default=31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"
X_FRAME_OPTIONS = "DENY"

# ─────────────────────────────────────────────
# CONTENT SECURITY POLICY (django-csp)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization",
    "content-type", "dnt", "origin", "user-agent",
    "x-csrftoken", "x-requested-with",
    "x-vault-token",                              # Custom vault auth header
    "x-device-fingerprint",                       # Anti-replay
]

# ─────────────────────────────────────────────
# CRYPTOGRAPHY SETTINGS
# ─────────────────────────────────────────────
AES_MASTER_KEY = bytes.fromhex(env("AES_MASTER_KEY"))
PQC_KYBER_PRIVATE_KEY_PATH = env("PQC_KYBER_PRIVATE_KEY_PATH")
PQC_DILITHIUM_PRIVATE_KEY_PATH = env("PQC_DILITHIUM_PRIVATE_KEY_PATH")

MESSAGE_DEFAULT_TTL_SECONDS = int(env("MESSAGE_DEFAULT_TTL_SECONDS", default=86400))
VAULT_SESSION_TTL_SECONDS = int(env("VAULT_SESSION_TTL_SECONDS", default=3600))

# ─────────────────────────────────────────────
# IPFS
# ─────────────────────────────────────────────
IPFS_API_URL = env("IPFS_API_URL", default="http://127.0.0.1:5001")
IPFS_GATEWAY = env("IPFS_GATEWAY", default="https://ipfs.io/ipfs/")

# ─────────────────────────────────────────────
# DAPI SPECTACULAR (Swagger)
# ─────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "SecureBank Messaging API",
    "DESCRIPTION": "Enterprise Banking Communication Platform — Ultra-Secure",
    "VERSION": "2.0.0",
    "CONTACT": {"email": "apiteam@yourbank.com"},
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
}

# ─────────────────────────────────────────────
# LOGGING — Structured, no sensitive data leakage
# ─────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "sanitize": {"()": "apps.compliance.middleware_forensics.SanitizeLogFilter"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "audit.log",
            "maxBytes": 10_000_000,
            "backupCount": 30,
            "filters": ["sanitize"],
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING"},
        "apps.users": {"handlers": ["audit_file"], "level": "INFO", "propagate": False},
        "apps.vault": {"handlers": ["audit_file"], "level": "DEBUG", "propagate": False},
        "apps.compliance": {"handlers": ["audit_file"], "level": "DEBUG", "propagate": False},
    },
}

# ─────────────────────────────────────────────
# PASSWORD VALIDATION
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 16}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.users.validators.BankPasswordComplexityValidator"},
]

# ─────────────────────────────────────────────
# STATIC & MEDIA
# ─────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── CSP v4.0 format ──
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'",
                      "https://cdn.tailwindcss.com",
                      "https://cdn.jsdelivr.net",
                      "https://fonts.googleapis.com"),
        'style-src': ("'self'", "'unsafe-inline'",
                     "https://fonts.googleapis.com",
                     "https://fonts.gstatic.com",
                     "https://cdn.jsdelivr.net"),
        'font-src': ("'self'",
                    "https://fonts.gstatic.com",
                    "https://cdn.jsdelivr.net",
                    "data:"),
        'img-src': ("'self'", "data:", "blob:"),
        'connect-src': ("'self'", "wss:", "ws:",
                       "https://cdn.tailwindcss.com",
                       "https://cdn.jsdelivr.net"),
        'frame-src': ("'none'",),
        'object-src': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    }
}
STATICFILES_DIRS = [BASE_DIR / 'static']



# Multi-Database — 20 databases
DATABASES["db_1"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_1",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_2"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_2",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_3"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_3",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_4"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_4",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_5"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_5",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_6"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_6",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_7"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_7",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_8"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_8",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_9"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_9",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_10"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_10",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_11"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_11",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_12"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_12",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_13"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_13",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_14"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_14",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_15"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_15",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_16"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_16",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_17"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_17",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_18"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_18",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_19"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_19",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}
DATABASES["db_20"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": "blackmess_db_20",
    "USER": env("DB_USER"),
    "PASSWORD": env("DB_PASSWORD"),
    "HOST": env("DB_HOST"),
    "PORT": env("DB_PORT"),
    "OPTIONS": {"sslmode": "disable"},
}

# Session Security Tambahan
MAX_CONCURRENT_SESSIONS = 3  # Max 3 session per user
SESSION_COOKIE_AGE = 28800   # 8 jam
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
