# Updated Settings

# Removed duplicate AUTH_USER_MODEL
AUTH_USER_MODEL = 'your_app.User'

# Removed duplicate AUTHENTICATION_BACKENDS
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
]

# Removed duplicate SOCIAL_AUTH_PIPELINE
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.social_auth.save_user',
]

# Merged SPECTACULAR_SETTINGS dictionaries
SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'DESCRIPTION': 'API description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {},
    'SWAGGER_UI_DIST': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/',
    'SWAGGER_UI_FAVICON_HREF': None,
    'REDOC_DIST': 'https://cdn.redoc.ly/redoc/latest/redoc.standalone.js',
}