from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OJKIncidentViewSet, InformationBarrierViewSet, RemoteWipeViewSet,
    SecureFileLinkViewSet, DLPRuleViewSet, HelpdeskTicketViewSet,
    InstitutionBadgeViewSet,
)

router = DefaultRouter()
router.register(r'ojk-incidents', OJKIncidentViewSet, basename='ojk-incident')
router.register(r'info-barriers', InformationBarrierViewSet, basename='info-barrier')
router.register(r'remote-wipe', RemoteWipeViewSet, basename='remote-wipe')
router.register(r'secure-links', SecureFileLinkViewSet, basename='secure-link')
router.register(r'dlp-rules', DLPRuleViewSet, basename='dlp-rule')
router.register(r'helpdesk', HelpdeskTicketViewSet, basename='helpdesk')
router.register(r'institution-badges', InstitutionBadgeViewSet, basename='institution-badge')

urlpatterns = [
    path('', include(router.urls)),
]
