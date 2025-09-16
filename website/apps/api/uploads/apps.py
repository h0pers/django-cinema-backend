from django.apps import AppConfig


class UploadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api.uploads'

    def ready(self):
        pass
