from django.urls import path
from .otp_views import send_otp, verify_otp, send_invite
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, RegisterView,
    MeProfileView, ChangePasswordView,
    SessionListView, PublicKeyView,
    MFASetupView, MFAVerifyView,
)

urlpatterns = [
    path('otp/send/', send_otp, name='send-otp'),
    path('otp/verify/', verify_otp, name='verify-otp'),
    path('invite/send/', send_invite, name='send-invite'),
    path('login/',           LoginView.as_view(),         name='login'),
    path('logout/',          LogoutView.as_view(),         name='logout'),
    path('register/',        RegisterView.as_view(),       name='register'),
    path('refresh/',         TokenRefreshView.as_view(),   name='token-refresh'),
    path('me/profile/',      MeProfileView.as_view(),      name='me-profile'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),
    path('sessions/',        SessionListView.as_view(),    name='sessions'),
    path('public-keys/',     PublicKeyView.as_view(),      name='public-keys'),
    path('mfa/setup/',       MFASetupView.as_view(),       name='mfa-setup'),
    path('mfa/verify/',      MFAVerifyView.as_view(),      name='mfa-verify'),
]
