from django.apps import AppConfig

class ComplianceConfig(AppConfig):
    name = r'apps.compliance'
    default_auto_field = r'django.db.models.BigAutoField'

    def ready(self):
        import apps.compliance.signals  # noqa
