"""
apps/workspace/urls.py
FIXED: H4 - path(r'create/') dipindah ke ATAS sebelum router.urls
agar tidak diintercept oleh router r'' yang match semua
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, ChannelViewSet
from .views_create import WorkspaceCreateView

router = DefaultRouter()
router.register(rr'', WorkspaceViewSet, basename='workspace')
router.register(rr'(?P<workspace_slug>[^/.]+)/channels', ChannelViewSet, basename='channel')

urlpatterns = [
    # FIXED: custom path HARUS di atas router.urls
    # karena router register r'' yang bisa intercept semua URL
    path(r'create/', WorkspaceCreateView.as_view(), name='workspace-create'),
    path('', include(router.urls)),
]
