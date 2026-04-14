from django.urls import path
from .otp_views import send_otp, verify_otp, send_invite, generate_totp_secret, verify_totp_setup
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, LogoutView, RegisterView, MeProfileView, ChangePasswordView, SessionListView, PublicKeyView, MFASetupView, MFAVerifyView
from .webauthn_views import WebAuthnRegisterBeginView, WebAuthnRegisterCompleteView, WebAuthnAuthBeginView, WebAuthnAuthCompleteView
from .settings_views import SettingsView, NotificationSettingsView, AppearanceSettingsView, SecuritySettingsView, RevokeSessionView, RemoveMFADeviceView, APIKeySettingsView, PrivacySettingsView

urlpatterns = [
    path(r'otp/send/', send_otp, name='send-otp'),
    path(r'otp/verify/', verify_otp, name='verify-otp'),
    path(r'invite/send/', send_invite, name='send-invite'),
    path(r'totp/generate/', generate_totp_secret, name='generate-totp'),
    path(r'totp/verify-setup/', verify_totp_setup, name='verify-totp-setup'),
    path(r'login/', LoginView.as_view(), name='login'),
    path(r'logout/', LogoutView.as_view(), name='logout'),
    path(r'register/', RegisterView.as_view(), name='register'),
    path(r'refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path(r'me/profile/', MeProfileView.as_view(), name='me-profile'),
    path(r'password/change/', ChangePasswordView.as_view(), name='password-change'),
    path(r'sessions/', SessionListView.as_view(), name='sessions'),
    path(r'public-keys/', PublicKeyView.as_view(), name='public-keys'),
    path(r'mfa/setup/', MFASetupView.as_view(), name='mfa-setup'),
    path(r'mfa/verify/', MFAVerifyView.as_view(), name='mfa-verify'),
    path(r'webauthn/register/begin/', WebAuthnRegisterBeginView.as_view(), name='webauthn-register-begin'),
    path(r'webauthn/register/complete/', WebAuthnRegisterCompleteView.as_view(), name='webauthn-register-complete'),
    path(r'webauthn/auth/begin/', WebAuthnAuthBeginView.as_view(), name='webauthn-auth-begin'),
    path(r'webauthn/auth/complete/', WebAuthnAuthCompleteView.as_view(), name='webauthn-auth-complete'),
    path(r'settings/', SettingsView.as_view(), name='settings'),
    path(r'settings/notifications/', NotificationSettingsView.as_view(), name='settings-notif'),
    path(r'settings/appearance/', AppearanceSettingsView.as_view(), name='settings-appearance'),
    path(r'settings/security/', SecuritySettingsView.as_view(), name='settings-security'),
    path(r'settings/security/revoke/', RevokeSessionView.as_view(), name='settings-revoke'),
    path(r'settings/security/mfa/<uuid:device_id>/remove/', RemoveMFADeviceView.as_view(), name='settings-mfa-remove'),
    path(r'settings/api-keys/', APIKeySettingsView.as_view(), name='settings-apikeys'),
    path(r'settings/privacy/', PrivacySettingsView.as_view(), name='settings-privacy'),
]
