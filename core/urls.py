"""
core/urls.py
Master URL configuration — 70 endpoints across 5 apps.
Three Swagger/OpenAPI portals: Admin, Internal, Client.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# ─────────────────────────────────────────────
# OpenAPI schema endpoints (one per audience)
# ─────────────────────────────────────────────
schema_patterns = [
    # Raw schema JSON/YAML
    path("api/schema/admin/",    SpectacularAPIView.as_view(urlconf="core.urls_admin"),    name="schema-admin"),
    path("api/schema/internal/", SpectacularAPIView.as_view(urlconf="core.urls_internal"), name="schema-internal"),
    path("api/schema/client/",   SpectacularAPIView.as_view(urlconf="core.urls_client"),   name="schema-client"),
    # Swagger UI
    path("api/docs/admin/",    SpectacularSwaggerView.as_view(url_name="schema-admin"),    name="swagger-admin"),
    path("api/docs/internal/", SpectacularSwaggerView.as_view(url_name="schema-internal"), name="swagger-internal"),
    path("api/docs/client/",   SpectacularSwaggerView.as_view(url_name="schema-client"),   name="swagger-client"),
    # ReDoc UI
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema-admin"), name="redoc"),
]

# ─────────────────────────────────────────────
# API v1 routes — all 70 endpoints
# ─────────────────────────────────────────────
api_v1 = [
    # ── Auth & Users (14 endpoints) ─────────────
    path("auth/",       include("apps.users.urls")),

    # ── Workspace (15 endpoints) ─────────────────
    path("workspaces/", include("apps.workspace.urls")),

    # ── Messaging (18 endpoints) ──────────────────
    path("msg/",        include("apps.messaging.urls")),

    # ── Vault (13 endpoints) ──────────────────────
    path("vault/",      include("apps.vault.urls")),

    # ── Compliance (10 endpoints) ─────────────────
    path("compliance/", include("apps.compliance.urls")),
]

urlpatterns = [
    path("api/v1/health/", health_check),
    # Django admin (hardened — custom URL slug)
    path("_bank_admin_7x9q/", admin.site.urls),

    # API v1
    path("api/v1/", include((api_v1, "api_v1"))),

    # OpenAPI / Swagger docs
    *schema_patterns,

    # Social Auth (OAuth2 / SSO)
    path("oauth/", include("social_django.urls", namespace="social")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
