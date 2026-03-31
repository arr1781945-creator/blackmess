from django.http import HttpResponseRedirect
from django.conf import settings


def oauth_callback(request):
    """Ambil JWT dari session lalu redirect ke frontend dengan token."""
    access = request.session.pop('oauth_access', None)
    refresh = request.session.pop('oauth_refresh', None)

    frontend = settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL

    if not access:
        return HttpResponseRedirect(f"{frontend}/auth/error?reason=oauth_failed")

    return HttpResponseRedirect(
        f"{frontend}/auth/callback?access={access}&refresh={refresh}"
    )
