from social_core.backends.github import GithubOAuth2

CALLBACK = 'https://black-message-production.up.railway.app/oauth/complete/github/'

class GithubOAuth2HTTPS(GithubOAuth2):
    REDIRECT_STATE = False

    def get_redirect_uri(self, state=None):
        return CALLBACK

    def auth_url(self):
        url = super().auth_url()
        return url.replace(
            'http://black-message-production.up.railway.app',
            'https://black-message-production.up.railway.app'
        )
