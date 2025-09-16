from rest_framework.viewsets import ModelViewSet

from apps.api.mixins import VersioningAPIViewMixin

from .filters import GenreFilterSet
from .models import Genre
from .v1.serializers import GenreSerializer


class GenreViewSet(VersioningAPIViewMixin, ModelViewSet):
    queryset = Genre.objects.all()
    filterset_class = GenreFilterSet
    lookup_url_kwarg = "slug"
    lookup_field = "slug"
    version_map = {
        "v1": {
            "serializer_class": GenreSerializer,
        }
    }
