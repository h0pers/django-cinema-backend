from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from apps.api.cinema.videos.mixins import TogglWatchViewSetMixin
from apps.api.mixins import VersioningAPIViewMixin

from .filters import EpisodeFilterSet
from .models import Episode
from .v1.serializers import EpisodeSerializer


class EpisodeViewSet(
    VersioningAPIViewMixin,
    TogglWatchViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Episode.objects.all()
    filterset_class = EpisodeFilterSet
    version_map = {
        "v1": {
            "serializer_class": EpisodeSerializer,
        }
    }
