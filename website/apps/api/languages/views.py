from rest_framework.viewsets import ModelViewSet

from apps.api.languages.filters import LanguageFilterSet
from apps.api.languages.v1.serializers import LanguageSerializer
from apps.api.mixins import VersioningAPIViewMixin
from apps.core.models import Language


class LanguageViewSet(VersioningAPIViewMixin, ModelViewSet):
    queryset = Language.objects.all()
    filterset_class = LanguageFilterSet
    lookup_field = "code"
    lookup_url_kwarg = "code"
    version_map = {
        "v1": {
            "serializer_class": LanguageSerializer,
        }
    }
