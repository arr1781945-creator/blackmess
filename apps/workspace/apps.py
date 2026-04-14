from django.apps import AppConfig

class WorkspaceConfig(AppConfig):
    name = r'apps.workspace'
    default_auto_field = r'django.db.models.BigAutoField'

    def ready(self):
        import apps.workspace.signals  # noqa
