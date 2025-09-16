from rest_framework.permissions import DjangoModelPermissions, IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.api.mixins import VersioningAPIViewMixin

from .filters import TransactionFilterSet
from .models import Transaction
from .v1.serializers import TransactionSerializer, TransactionStaffSerializer


class TransactionViewSet(VersioningAPIViewMixin, ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    filterset_class = TransactionFilterSet
    version_map = {
        "v1": {
            "serializer_class": TransactionStaffSerializer
        }
    }

    def get_version_map(self):
        if self.action == "retrieve":
            if not self.request.user.is_staff:
                return {
                    "v1": {
                        "serializer_class": TransactionSerializer
                    }
                }
        return super().get_version_map()

    def get_queryset(self):
        if self.action == "retrieve":
            if not self.request.user.is_staff:
                return self.request.user.transactions.all()
        return super().get_queryset()

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
