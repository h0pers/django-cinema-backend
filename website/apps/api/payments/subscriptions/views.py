from rest_framework.viewsets import ModelViewSet

from apps.api.mixins import VersioningAPIViewMixin

from .filters import SubscriptionFilterSet
from .models import Subscription
from .v1.serializers import SubscriptionSerializer


class SubscriptionViewSet(VersioningAPIViewMixin, ModelViewSet):
    filterset_class = SubscriptionFilterSet
    version_map = {
        "v1": {
            "serializer_class": SubscriptionSerializer
        }
    }

    def get_queryset(self):
        if (
            not self.request.user or
            not self.request.user.is_authenticated or
            not self.request.user.is_staff
        ):
            return Subscription.public.all()
        return Subscription.objects.all()
