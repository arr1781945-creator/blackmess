from django.apps import AppConfig

class UsersConfig(AppConfig):
    name = r'apps.users'
    default_auto_field = r'django.db.models.BigAutoField'

    def ready(self):
        import apps.users.signals  # noqa
