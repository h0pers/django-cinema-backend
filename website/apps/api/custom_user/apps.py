from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomUserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api.custom_user'
    verbose_name = _('Customer')
    verbose_name_plural = _('Customers')

    def ready(self):
        pass
