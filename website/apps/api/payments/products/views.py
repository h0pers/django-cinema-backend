from rest_framework import viewsets

from apps.api.mixins import VersioningAPIViewMixin

from .filters import ProductFilterSet
from .models import Product
from .v1.serializers import ProductSerializerV1


class ProductViewSet(VersioningAPIViewMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    filterset_class = ProductFilterSet
    version_map = {
        "v1": ProductSerializerV1
    }

    def get_queryset(self):
        if (
            not self.request.user or
            not self.request.user.is_authenticated or
            not self.request.user.is_staff
        ):
          return Product.public.all()
        return super().get_queryset()
