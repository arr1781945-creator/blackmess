from django.apps import AppConfig

class MessagingConfig(AppConfig):
    name = r'apps.messaging'
    default_auto_field = r'django.db.models.BigAutoField'

    def ready(self):
        import apps.messaging.signals  # noqa
