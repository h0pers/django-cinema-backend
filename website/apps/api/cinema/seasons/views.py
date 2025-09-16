from rest_framework import mixins
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.viewsets import GenericViewSet

from apps.api.cinema.videos.mixins import TogglWatchViewSetMixin
from apps.api.mixins import VersioningAPIViewMixin

from .models import Season
from .v1.serializers import SeasonSerializer


class SeasonViewSet(
    VersioningAPIViewMixin,
    TogglWatchViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Season.objects.all()
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    version_map = {
        "v1": {
            "serializer_class": SeasonSerializer,
        }
    }

    def get_version_map(self):
        if self.action in ("retrieve",):
            return {
                "v1": {
                    "serializer_class": SeasonSerializer,
                }
            }
        return super().get_version_map()
