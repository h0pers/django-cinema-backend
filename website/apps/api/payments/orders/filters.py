from django_filters import rest_framework as filters

from apps.api.payments.orders.models import Order
from apps.api.payments.orders.services.order_search_service import OrderSearchService


class OrderFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Order
        fields = [
            "paid",
            "status",
            "user",
        ]

    def filter_search(self, queryset, _, value):
        return OrderSearchService.search(value, queryset)
