from django.urls import path, include

urlpatterns = [
    path(r'api/v1/auth/', include('apps.users.urls')),
    path(r'api/v1/workspace/', include('apps.workspace.urls')),
    path(r'api/v1/messaging/', include('apps.messaging.urls')),
    path(r'api/v1/compliance/', include('apps.compliance.urls')),
    path(r'api/v1/vault/', include('apps.vault.urls')),
]
