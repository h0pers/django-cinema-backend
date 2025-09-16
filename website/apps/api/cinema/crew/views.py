from rest_framework.viewsets import ModelViewSet

from apps.api.mixins import VersioningAPIViewMixin

from .filters import CrewMemberFilterSet
from .models import CrewMember
from .v1.serializers import CrewMemberSerializer


class CrewMemberViewSet(VersioningAPIViewMixin, ModelViewSet):
    queryset = CrewMember.objects.all()
    filterset_class = CrewMemberFilterSet
    version_map = {
        "v1": {
            "serializer_class": CrewMemberSerializer,
        }
    }
