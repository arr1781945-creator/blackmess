from django.apps import AppConfig

class VaultConfig(AppConfig):
    name = r'apps.vault'
    default_auto_field = r'django.db.models.BigAutoField'

    def ready(self):
        import apps.vault.signals  # noqa
