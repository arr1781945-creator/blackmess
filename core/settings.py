# Updated Settings

# Removed duplicate AUTH_USER_MODEL
AUTH_USER_MODEL = r'your_app.User'

# Removed duplicate AUTHENTICATION_BACKENDS
AUTHENTICATION_BACKENDS = [
    r'django.contrib.auth.backends.ModelBackend',
    r'social_core.backends.google.GoogleOAuth2',
    r'social_core.backends.github.GithubOAuth2',
]

# Removed duplicate SOCIAL_AUTH_PIPELINE
SOCIAL_AUTH_PIPELINE = [
    r'social_core.pipeline.social_auth.social_details',
    r'social_core.pipeline.social_auth.social_uid',
    r'social_core.pipeline.social_auth.auth_allowed',
    r'social_core.pipeline.social_auth.social_user',
    r'social_core.pipeline.user.get_username',
    r'social_core.pipeline.user.create_user',
    r'social_core.pipeline.social_auth.associate_user',
    r'social_core.pipeline.social_auth.load_extra_data',
    r'social_core.pipeline.social_auth.save_user',
]

# Merged SPECTACULAR_SETTINGS dictionaries
SPECTACULAR_SETTINGS = {
    r'TITLE': 'My API',
    r'DESCRIPTION': 'API description',
    r'VERSION': '1.0.0',
    r'SERVE_INCLUDE_SCHEMA': True,
    r'SWAGGER_UI_SETTINGS': {},
    r'SWAGGER_UI_DIST': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/',
    r'SWAGGER_UI_FAVICON_HREF': None,
    r'REDOC_DIST': 'https://cdn.redoc.ly/redoc/latest/redoc.standalone.js',
}