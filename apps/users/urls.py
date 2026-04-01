from django.urls import path
from .otp_views import send_otp, verify_otp, send_invite, generate_totp_secret, verify_totp_setup
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, RegisterView,
    MeProfileView, ChangePasswordView,
    SessionListView, PublicKeyView,
    MFASetupView, MFAVerifyView,
)
from .pq_mfa import (
    PQMFARegisterView, PQMFAChallengeView, PQMFAVerifyView,
)
from .webauthn_views import (
    WebAuthnRegisterBeginView, WebAuthnRegisterCompleteView,
    WebAuthnAuthBeginView, WebAuthnAuthCompleteView,
)
from .settings_views import (
    SettingsView, NotificationSettingsView, AppearanceSettingsView,
    SecuritySettingsView, RevokeSessionView, RemoveMFADeviceView,
    APIKeySettingsView, PrivacySettingsView,
)

urlpatterns = [
    path('otp/send/', send_otp, name='send-otp'),
    path('otp/verify/', verify_otp, name='verify-otp'),
    path('invite/send/', send_invite, name='send-invite'),
    path('totp/generate/', generate_totp_secret, name='generate-totp'),
    path('totp/verify-setup/', verify_totp_setup, name='verify-totp-setup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/profile/', MeProfileView.as_view(), name='me-profile'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),
    path('sessions/', SessionListView.as_view(), name='sessions'),
    path('public-keys/', PublicKeyView.as_view(), name='public-keys'),
    path('mfa/setup/', MFASetupView.as_view(), name='mfa-setup'),
    path('mfa/verify/', MFAVerifyView.as_view(), name='mfa-verify'),
    path('webauthn/register/begin/', WebAuthnRegisterBeginView.as_view(), name='webauthn-register-begin'),
    path('webauthn/register/complete/', WebAuthnRegisterCompleteView.as_view(), name='webauthn-register-complete'),
    path('webauthn/auth/begin/', WebAuthnAuthBeginView.as_view(), name='webauthn-auth-begin'),
    path('webauthn/auth/complete/', WebAuthnAuthCompleteView.as_view(), name='webauthn-auth-complete'),
    path('pq/register/', PQMFARegisterView.as_view(), name='pq-register'),
    path('pq/challenge/', PQMFAChallengeView.as_view(), name='pq-challenge'),
    path('pq/verify/', PQMFAVerifyView.as_view(), name='pq-verify'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('settings/notifications/', NotificationSettingsView.as_view(), name='settings-notif'),
    path('settings/appearance/', AppearanceSettingsView.as_view(), name='settings-appearance'),
    path('settings/security/', SecuritySettingsView.as_view(), name='settings-security'),
    path('settings/security/revoke/', RevokeSessionView.as_view(), name='settings-revoke'),
    path('settings/security/mfa/<uuid:device_id>/remove/', RemoveMFADeviceView.as_view(), name='settings-mfa-remove'),
    path('settings/api-keys/', APIKeySettingsView.as_view(), name='settings-apikeys'),
    path('settings/privacy/', PrivacySettingsView.as_view(), name='settings-privacy'),
]
