from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, ChannelViewSet
from .views_create import WorkspaceCreateView

router = DefaultRouter()
router.register(r'', WorkspaceViewSet, basename='workspace')
router.register(r'(?P<workspace_slug>[^/.]+)/channels', ChannelViewSet, basename='channel')

urlpatterns = [
    path('create/', WorkspaceCreateView.as_view(), name='workspace-create'),
    path('', include(router.urls)),
]
