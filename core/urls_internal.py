from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.workspace.urls')),
    path('api/v1/', include('apps.messaging.urls')),
    path('api/v1/', include('apps.compliance.urls')),
    path('api/v1/', include('apps.vault.urls')),
]
