from celery.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.api.cinema.videos.models import ToggleWatchModel
from apps.api.cinema.videos.services.toggle_watch_service import ToggleWatchService


class TogglWatchViewSetMixin:
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if self.action in ["enable_watch", "disable_watch"]:
            if not issubclass(obj.__class__, ToggleWatchModel):
                raise ImproperlyConfigured("Model object is not subclass of ToggleWatchModel")
        return obj

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path='enable',
        version_map=None
    )
    def enable_watch(self, request, *args, **kwargs):
        obj = self.get_object()

        self.check_object_permissions(request, obj)

        if obj.allowed_to_watch:
            raise ValidationError({
                "allowed_to_watch": _("%(model)s is already enabled") % {
                    "model": obj.__class__.__name__
                }
            })

        ToggleWatchService.enable(obj)
        return Response({"message": "Watch enabled"})

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=[IsAdminUser],
        url_path='disable',
        version_map=None
    )
    def disable_watch(self, request, *args, **kwargs):
        obj = self.get_object()

        self.check_object_permissions(request, obj)

        if not obj.allowed_to_watch:
            raise ValidationError({
                "allowed_to_watch": _("%(model)s is already disabled") % {
                    "model": obj.__class__.__name__
                }
            })

        ToggleWatchService.disable(obj)
        return Response({"message": "Watch disabled"})
