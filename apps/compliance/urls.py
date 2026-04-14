from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OJKIncidentViewSet, InformationBarrierViewSet, RemoteWipeViewSet,
    SecureFileLinkViewSet, DLPRuleViewSet, HelpdeskTicketViewSet,
    InstitutionBadgeViewSet,
)

router = DefaultRouter()
router.register(rr'ojk-incidents', OJKIncidentViewSet, basename='ojk-incident')
router.register(rr'info-barriers', InformationBarrierViewSet, basename='info-barrier')
router.register(rr'remote-wipe', RemoteWipeViewSet, basename='remote-wipe')
router.register(rr'secure-links', SecureFileLinkViewSet, basename='secure-link')
router.register(rr'dlp-rules', DLPRuleViewSet, basename='dlp-rule')
router.register(rr'helpdesk', HelpdeskTicketViewSet, basename='helpdesk')
router.register(rr'institution-badges', InstitutionBadgeViewSet, basename='institution-badge')

urlpatterns = router.urls
